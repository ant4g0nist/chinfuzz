from typing import Any, Dict, List, Optional, Tuple, Type, cast

from pytezos.context.impl import ExecutionContext
from pytezos.crypto.encoding import base58_encode
from pytezos.michelson.instructions.base import MichelsonInstruction, format_stdout
from pytezos.michelson.instructions.tzt import BigMapInstruction, StackEltInstruction
from pytezos.michelson.micheline import MichelineSequence, get_script_section, get_script_sections, try_catch, validate_sections
from pytezos.michelson.sections.code import CodeSection
from pytezos.michelson.sections.parameter import ParameterSection
from pytezos.michelson.sections.storage import StorageSection
from pytezos.michelson.sections.tzt import (
    AmountSection,
    BalanceSection,
    BigMapsSection,
    ChainIdSection,
    InputSection,
    NowSection,
    OutputSection,
    SelfSection,
    SenderSection,
    SourceSection,
)
from pytezos.michelson.sections.view import ViewSection
from pytezos.michelson.stack import MichelsonStack
from pytezos.michelson.types import ListType, MichelsonType, OperationType, PairType


class MichelsonProgram:
    """Michelson .tz contract interpreter interface"""

    parameter: Type[ParameterSection]
    storage: Type[StorageSection]
    code: Type[CodeSection]
    views: List[Type[ViewSection]]

    def __init__(self, name: str, parameter: ParameterSection, storage: StorageSection) -> None:
        self.name = name
        self.parameter_value = parameter
        self.storage_value = storage

    @staticmethod
    def load(context: ExecutionContext, with_code=False) -> Type['MichelsonProgram']:
        """Create MichelsonProgram type from filled context"""
        cls = type(
            MichelsonProgram.__name__,
            (MichelsonProgram,),
            dict(
                parameter=ParameterSection.match(context.get_parameter_expr()),
                storage=StorageSection.match(context.get_storage_expr()),
                code=CodeSection.match(context.get_code_expr() if with_code else []),
                views=[ViewSection.match(expr) for expr in context.get_views_expr()] if with_code else [],
            ),
        )
        return cast(Type['MichelsonProgram'], cls)

    @staticmethod
    def create(sequence: Type[MichelineSequence]) -> Type['MichelsonProgram']:
        """Create MichelsonProgram type from micheline"""
        validate_sections(
            sequence,
            (
                'parameter',
                'storage',
                'code',
            ),
        )
        cls = type(
            MichelsonProgram.__name__,
            (MichelsonProgram,),
            dict(
                parameter=get_script_section(sequence, cls=ParameterSection, required=True),  # type: ignore
                storage=get_script_section(sequence, cls=StorageSection, required=True),  # type: ignore
                code=get_script_section(sequence, cls=CodeSection, required=True),  # type: ignore
                views=get_script_sections(sequence, cls=ViewSection),  # type: ignore
            ),
        )
        return cast(Type['MichelsonProgram'], cls)

    @staticmethod
    def match(expr) -> Type['MichelsonProgram']:
        seq = cast(Type[MichelineSequence], MichelineSequence.match(expr))
        if not issubclass(seq, MichelineSequence):
            raise Exception(f'Expected sequence, got {seq.prim}')
        return MichelsonProgram.create(seq)

    @classmethod
    def as_micheline_expr(cls) -> List[Dict[str, Any]]:
        return [
            cls.parameter.as_micheline_expr(),
            cls.storage.as_micheline_expr(),
            cls.code.as_micheline_expr(),
            *[view.as_micheline_expr() for view in cls.views],
        ]

    @classmethod
    def get_view(cls, name: str) -> Type[ViewSection]:
        return next(view for view in cls.views if view.name == name)

    @classmethod
    def instantiate(cls, entrypoint: str, parameter, storage) -> 'MichelsonProgram':
        parameter_value = cls.parameter.from_parameters(dict(entrypoint=entrypoint, value=parameter))
        storage_value = cls.storage.from_micheline_value(storage)
        return cls(entrypoint, parameter_value, storage_value)

    @classmethod
    def instantiate_view(cls, name: str, parameter, storage) -> 'MichelsonProgram':
        view = cls.get_view(name)
        parameter_ty = ParameterSection.create_type(args=[view.args[1]])
        parameter_value = parameter_ty.from_micheline_value(parameter)
        storage_value = cls.storage.from_micheline_value(storage)
        return cls(name, parameter_value, storage_value)

    @try_catch('BEGIN')
    def begin(self, stack: MichelsonStack, stdout: List[str], context: ExecutionContext) -> None:
        """Prepare stack for contract execution"""
        self.parameter_value.attach_context(context)
        self.storage_value.attach_context(context)
        res = PairType.from_comb([self.parameter_value.item, self.storage_value.item])
        stack.push(res)
        stdout.append(format_stdout(f'BEGIN %{self.name}', [], [res]))

    def execute(self, stack: MichelsonStack, stdout: List[str], context: ExecutionContext) -> MichelsonInstruction:
        """Execute contract in interpreter"""
        return cast(MichelsonInstruction, self.code.args[0].execute(stack, stdout, context))

    def execute_view(self, stack: MichelsonStack, stdout: List[str], context: ExecutionContext):
        """Execute view in interpreter"""
        view = self.get_view(self.name)
        return cast(MichelsonInstruction, view.args[3].execute(stack, stdout, context))

    @try_catch('END')
    def end(self, stack: MichelsonStack, stdout: List[str], output_mode='readable') -> Tuple[List[dict], Any, List[dict], PairType]:
        """Finish contract execution"""
        res = cast(PairType, stack.pop1())
        if len(stack):
            raise Exception(f'Stack is not empty: {repr(stack)}')
        res.assert_type_equal(
            PairType.create_type(
                args=[ListType.create_type(args=[OperationType]), self.storage.args[0]],
            ),
            message='list of operations + resulting storage',
        )
        operations = [op.content for op in res.items[0]]  # type: ignore
        lazy_diff = []  # type: ignore
        storage = res.items[1].aggregate_lazy_diff(lazy_diff).to_micheline_value(mode=output_mode)
        stdout.append(format_stdout(f'END %{self.name}', [res], []))
        return operations, storage, lazy_diff, res

    @try_catch('RET')
    def ret(self, stack: MichelsonStack, stdout: List[str], output_mode='readable') -> MichelsonType:
        view = self.get_view(self.name)
        res = stack.pop1()
        if len(stack):
            raise Exception(f'Stack is not empty: {repr(stack)}')
        res.assert_type_equal(view.args[2], message='view return type')
        stdout.append(format_stdout(f'RET %{self.name}', [res], []))
        return view.args[2].from_micheline_value(res.to_micheline_value(mode=output_mode))


class TztMichelsonProgram:
    """Michelson .tzt contract interpreter interface"""

    code: Type[CodeSection]
    input: Type[InputSection]
    output: Type[OutputSection]
    big_maps: Optional[Type[BigMapsSection]]

    @staticmethod
    def load(context: ExecutionContext, with_code=False):
        """Create TztMichelsonProgram type from filled context"""
        cls = type(
            TztMichelsonProgram.__name__,
            (TztMichelsonProgram,),
            dict(
                input=InputSection.match(context.get_input_expr()),
                output=OutputSection.match(context.get_output_expr()),
                code=CodeSection.match(context.get_code_expr() if with_code else []),
                big_maps=BigMapsSection.match(context.get_big_maps_expr()) if context.get_big_maps_expr() else None,
            ),
        )
        return cast(Type['TztMichelsonProgram'], cls)

    @staticmethod
    def create(sequence: Type[MichelineSequence]) -> Type['TztMichelsonProgram']:
        """Create TztMichelsonProgram type from micheline"""
        validate_sections(sequence, ('input', 'output', 'code'))
        cls = type(
            TztMichelsonProgram.__name__,
            (TztMichelsonProgram,),
            dict(
                input=get_script_section(sequence, cls=InputSection, required=True),  # type: ignore
                output=get_script_section(sequence, cls=OutputSection, required=True),  # type: ignore
                code=get_script_section(sequence, cls=CodeSection, required=True),  # type: ignore
                big_maps=get_script_section(sequence, cls=BigMapsSection, required=False),  # type: ignore
            ),
        )
        return cast(Type['TztMichelsonProgram'], cls)

    @staticmethod
    def match(expr) -> Type['TztMichelsonProgram']:
        seq = cast(Type[MichelineSequence], MichelineSequence.match(expr))
        if not issubclass(seq, MichelineSequence):
            raise Exception(f'expected sequence, got {seq.prim}')
        return TztMichelsonProgram.create(seq)

    @classmethod
    def as_micheline_expr(cls) -> List[Dict[str, Any]]:
        # TODO: Serialize all sections
        return [
            cls.code.as_micheline_expr(),
            cls.input.as_micheline_expr(),
            cls.output.as_micheline_expr(),
        ]

    @classmethod
    def instantiate(cls) -> 'TztMichelsonProgram':
        return cls()

    def fill_context(self, script, context: ExecutionContext) -> None:
        sender = context.get_sender_expr()
        if sender:
            context.sender = SenderSection.match(sender).args[0].get_string()  # type: ignore
        amount = context.get_amount_expr()
        if amount:
            context.amount = AmountSection.match(amount).args[0].get_int()  # type: ignore
        balance = context.get_balance_expr()
        if balance:
            context.balance = BalanceSection.match(balance).args[0].get_int()  # type: ignore
        _self = context.get_self_expr()
        if _self:
            context.address = SelfSection.match(_self).args[0].get_string()  # type: ignore
        now = context.get_now_expr()
        if now:
            context.now = NowSection.match(now).args[0].get_int()  # type: ignore
        source = context.get_source_expr()
        if source:
            context.source = SourceSection.match(source).args[0].get_string()  # type: ignore
        chain_id = context.get_chain_id_expr()
        if chain_id:
            # FIXME: Move to some common place
            context.chain_id = base58_encode(
                cast(bytes, ChainIdSection.match(chain_id).args[0].literal),
                prefix=b'Net',
            ).decode()

    def register_bigmaps(self, stack: MichelsonStack, stdout: List[str], context: ExecutionContext) -> None:
        if self.big_maps:
            for item in self.big_maps.args[0].args[::-1]:
                if not issubclass(item, BigMapInstruction):
                    raise Exception('Only `Big_map` instructions can be used in `big_maps` section')
                item.add(stack, stdout, context)

    def begin(self, stack: MichelsonStack, stdout: List[str], context: ExecutionContext) -> None:  # pylint: disable=no-self-use
        """Prepare stack for contract execution"""

        for item in self.input.args[0].args[::-1]:
            if issubclass(item, StackEltInstruction):
                item.push(stack, stdout, context)
            else:
                raise Exception('Only `Stack_elt` instructions can be used in `input` section', item)

    def execute(self, stack: MichelsonStack, stdout: List[str], context: ExecutionContext) -> MichelsonInstruction:
        """Execute contract in interpreter"""
        return cast(MichelsonInstruction, self.code.args[0].execute(stack, stdout, context))

    def end(self, stack: MichelsonStack, stdout: List[str], context: ExecutionContext) -> None:
        """Finish contract execution"""
        for item in self.output.args[0].args:
            if not issubclass(item, StackEltInstruction):
                raise Exception('Only `Stack_elt` instructions can be used in `output` section')
            item.pull(stack, stdout, context)

        if len(stack):
            raise Exception('Stack is not empty after processing `output` section')

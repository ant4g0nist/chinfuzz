# Inspired by https://github.com/jansorg/tezos-intellij/blob/master/grammar/michelson.bnf
import json
import re
from typing import List, Optional

from ply.lex import Lexer  # type: ignore
from ply.lex import LexToken, lex
from ply.yacc import yacc  # type: ignore

from pytezos.michelson.macros import expand_macro
from pytezos.michelson.macros import expr as make_expr
from pytezos.michelson.tags import prim_tags


class MichelsonParserError(ValueError):

    def __init__(self, token: LexToken, message=None):
        message = message or f'failed to parse expression {token}'
        super(MichelsonParserError, self).__init__(message)
        self.message = message
        self.line = token.lineno
        self.pos = token.lexpos

    def format_stdout(self) -> str:
        return f'{self.line}:{self.pos}: {self.message}'


class Sequence(list):
    pass


class SimpleMichelsonLexer(Lexer):
    tokens = ('INT', 'BYTE', 'STR', 'ANNOT', 'PRIM',
              'LEFT_CURLY', 'RIGHT_CURLY', 'LEFT_PAREN', 'RIGHT_PAREN', 'SEMI')

    t_INT = r'-?[0-9]+'
    t_BYTE = r'0x[A-Fa-f0-9]*'
    t_STR = r'\"(\\.|[^\"])*\"'
    t_ANNOT = r'[:@%]+([_0-9a-zA-Z\.]*)?'  # r'[:@%]+([_a-zA-Z][_0-9a-zA-Z\.]*)?'
    t_PRIM = r'[A-Za-z][A-Za-z0-9_]+'
    t_LEFT_CURLY = r'\{'
    t_RIGHT_CURLY = r'\}'
    t_LEFT_PAREN = r'\('
    t_RIGHT_PAREN = r'\)'
    t_SEMI = r';'

    t_ignore_MULTI_COMMENT = r'/\*[^*]*\*/'
    t_ignore_COMMENT = r'#[^\n]*'
    t_ignore = ' \t\r\n\f'

    def __init__(self):
        super(SimpleMichelsonLexer, self).__init__()
        self.lexer = lex(module=self, reflags=re.MULTILINE)

    def t_error(self, t):
        t.type = t.value[0]
        t.value = t.value[0]
        t.lexer.skip(1)
        return t


class MichelsonParser(object):
    """ Customizable Michelson parser
    """
    tokens = SimpleMichelsonLexer.tokens

    def p_instr(self, p):
        '''instr : expr
                 | empty
        '''
        p[0] = p[1]

    def p_instr_int(self, p):
        '''instr : INT'''
        p[0] = {'int': p[1]}

    def p_instr_byte(self, p):
        '''instr : BYTE'''
        p[0] = {'bytes': p[1][2:]}  # strip 0x prefix

    def p_instr_str(self, p):
        '''instr : STR'''
        p[0] = {'string': json.loads(p[1])}

    def p_instr_list(self, p):
        '''instr : instr SEMI instr'''
        p[0] = list()
        for i in [p[1], p[3]]:
            if type(i) is list:
                p[0].extend(i)
            elif i is not None:
                p[0].append(i)

    def p_instr_subseq(self, p):
        '''instr : LEFT_CURLY instr RIGHT_CURLY'''
        p[0] = Sequence()
        if type(p[2]) is list:
            p[0].extend(p[2])
        elif p[2] is not None:
            p[0].append(p[2])

    def p_expr(self, p):
        '''expr : PRIM annots args'''
        prim = p[1]
        if prim in prim_tags or prim in self.extra_primitives:
            expr = make_expr(
                prim=prim, 
                annots=p[2] or [], 
                args=p[3] or []
            )
        else:
            try:
                expr = expand_macro(
                    prim=prim,
                    annots=p[2] or [],
                    args=p[3] or []
                )
            except AssertionError as e:
                raise MichelsonParserError(p.slice[1], str(e)) from e
        p[0] = Sequence(expr) if isinstance(expr, list) else expr

    def p_annots(self, p):
        '''annots : annot
                  | empty
        '''
        if p[1] is not None:
            p[0] = [p[1]]

    def p_annots_list(self, p):
        '''annots : annots annot'''
        p[0] = list()
        if type(p[1]) == list:
            p[0].extend(p[1])
        if p[2] is not None:
            p[0].append(p[2])

    def p_annot(self, p):
        '''annot : ANNOT'''
        p[0] = p[1]

    def p_args(self, p):
        '''args : arg
                | empty
        '''
        p[0] = list()
        if p[1] is not None:
            p[0].append(p[1])

    def p_args_list(self, p):
        '''args : args arg'''
        p[0] = list()
        if type(p[1]) == list:
            p[0].extend(p[1])
        if p[2] is not None:
            p[0].append(p[2])

    def p_arg_prim(self, p):
        '''arg : PRIM'''
        p[0] = {'prim': p[1]}

    def p_arg_int(self, p):
        '''arg : INT'''
        p[0] = {'int': p[1]}

    def p_arg_byte(self, p):
        '''arg : BYTE'''
        p[0] = {'bytes': p[1][2:]}  # strip 0x prefix

    def p_arg_str(self, p):
        '''arg : STR'''
        p[0] = {'string': json.loads(p[1])}

    def p_arg_subseq(self, p):
        '''arg : LEFT_CURLY instr RIGHT_CURLY'''
        if type(p[2]) == list:
            p[0] = p[2]
        elif p[2] is not None:
            p[0] = [p[2]]
        else:
            p[0] = []

    def p_arg_group(self, p):
        '''arg : LEFT_PAREN expr RIGHT_PAREN'''
        p[0] = p[2]

    def p_empty(self, p):
        '''empty :'''

    def p_error(self, p):
        raise MichelsonParserError(p)

    def __init__(self, debug=False, write_tables=False, extra_primitives: Optional[List[str]] = None):
        """ Initialize Michelson parser

        :param debug: Verbose output
        :param write_tables: Store PLY output
        :param extra_primitives: List of words to be ignored
        """
        self.lexer = SimpleMichelsonLexer()
        self.parser = yacc(
            module=self,
            debug=debug,
            write_tables=write_tables,
        )
        self.extra_primitives = extra_primitives or []

    def parse(self, code):
        """ Parse Michelson source.

        :param code: Michelson source
        :returns: Micheline expression
        """
        if len(code) > 0 and code[0] == '(' and code[-1] == ')':
            code = code[1:-1]
        return self.parser.parse(code)


def michelson_to_micheline(data, parser=None):
    """ Converts Michelson source text into a Micheline expression.

    :param data: Michelson string
    :param parser: custom Michelson parser (optional)
    :returns: Micheline expression
    """
    if parser is None:
        parser = MichelsonParser()
    return parser.parse(data)

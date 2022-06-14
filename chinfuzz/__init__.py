#!/usr/bin/env python3
import os
import sys
import rich
import pathlib
import argparse
import warnings
from rich import pretty

import io
import halo
import atheris
import contextlib

def chinfuzzInitialize(args, env):
    from chinstrap import helpers
    from chinstrap import chinstrapInitialize

    chinstrapInitialize(args, env)
    targetPath = pathlib.Path(f"{os.getcwd()}")
    os.makedirs(f"{targetPath}/fuzz", exist_ok=True)

    chinfuzzPath = os.path.dirname(os.path.abspath(__file__))

    helpers.copyFile(
            f"{chinfuzzPath}/resources/fuzz/SampleContractFuzzer.py",
            f"{targetPath}/fuzz/SampleContractFuzzer.py",
        )

def chinfuzzStartFuzzer(args, env):
    
    from chinfuzz.core import fuzz
    
    _fuzz  = fuzz.ChinFuzz(args)

    spinner = halo.Halo(text=f"Initializing fuzzer...", spinner="dots")
    spinner.start()

    with io.StringIO() as buff:
        with contextlib.redirect_stderr(buff):
            with atheris.instrument_imports():
                import chinstrap
                from chinfuzz.thirdparty.pytezos import pytezos

    spinner.succeed(text="Fuzzer initialized")

    _fuzz.runOneFuzzer(lib_fuzzer_args=lib_fuzzer_args)


def chinfuzzReplayFuzzer(args, env):

    from chinfuzz.core import fuzz
    _fuzz  = fuzz.ChinFuzz(args)

    _fuzz.replayFuzzerWithPoC()

def welcome_banner():
    banner="""
      _     _        __               
     | |   (_)      / _|              
  ___| |__  _ _ __ | |_ _   _ ________
 / __| '_ \| | '_ \|  _| | | |_  /_  /
| (__| | | | | | | | | | |_| |/ / / / 
 \___|_| |_|_|_| |_|_|  \__,_/___/___|
"""
    print(banner)

def main(args, env=os.environ):
    pretty.install()
    welcome_banner()
    
    parser = argparse.ArgumentParser(
        description=rich.print(
            ":penguin:",
            "[bold green]Chinfuzz - a code coverage \
fuzzer framework for Tezos smart contracts[/bold green]!",
        )
    )
    subparsers = parser.add_subparsers()

    parser_a = subparsers.add_parser("init", help="Initialize a new Chinfuzz project")
    parser_a.add_argument(
        "-f",
        "--force",
        default=False,
        action="store_true",
        help="Force initialize Chinfuzz project in the current directory. \
Be careful, this will potentioally overwrite files that exist in the directory.",
    )
    parser_a.set_defaults(func=chinfuzzInitialize)

    parser_b = subparsers.add_parser("fuzz", help="Runs a given fuzzer")
    parser_b.add_argument(
        "-f",
        "--fuzz",
        required=True,
        help="Fuzzer to run",
    )

    parser_b.add_argument(
        "-c",
        "--corpus",
        help="corpus folder",
    )

    parser_b.set_defaults(func=chinfuzzStartFuzzer)

    parser_c = subparsers.add_parser("replay", help="Replay a given PoC")
    parser_c.add_argument(
        "-p",
        "--poc",
        required=True,
        help="Proof of concept file to run. This file is run against the given fuzzer",
    )

    parser_c.add_argument(
        "-f",
        "--fuzz",
        required=True,
        help="Fuzzer to run.",
    )
    parser_c.set_defaults(func=chinfuzzReplayFuzzer)


    if not args[1:]:
        parser.print_help()
        exit(1)

    # this is an 'internal' method
    args, unknown = parser.parse_known_args()
    global lib_fuzzer_args
    lib_fuzzer_args = []
    for arg in unknown:
        if arg == "--":
            lib_fuzzer_args = unknown[unknown.index(arg)+1:]
            break

    return args.func(args, env)

if __name__ == "__main__":
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=SyntaxWarning)
        exit(main(sys.argv))

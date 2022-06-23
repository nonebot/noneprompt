from typing import Dict, Callable
from argparse import ArgumentParser

parser = ArgumentParser(prog="noneprompt", description="A simple prompt toolkit.")
parser.add_argument(
    "--no-ansi", action="store_true", required=False, help="disable ANSI colors"
)
parser.add_argument(
    "-d", "--default", required=False, help="default answer when cancelled"
)

subparsers = parser.add_subparsers(title="prompt type", dest="type", required=True)

from .list import list_prompt_main
from .input import input_prompt_main
from .confirm import confirm_prompt_main
from .checkbox import checkbox_prompt_main

PROMPT_TYPES: Dict[str, Callable] = {
    "input": input_prompt_main,
    "confirm": confirm_prompt_main,
    "checkbox": checkbox_prompt_main,
    "list": list_prompt_main,
}


def main():
    result = parser.parse_args()
    result = vars(result)
    prompt = PROMPT_TYPES[result.pop("type")]
    prompt(**result)

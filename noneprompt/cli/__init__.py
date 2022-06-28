from typing import Dict, Callable
from argparse import ArgumentParser

parser = ArgumentParser(prog="noneprompt", description="A simple prompt toolkit.")
parser.add_argument(
    "--no-ansi", action="store_true", required=False, help="disable ANSI colors"
)
parser.add_argument(
    "-d", "--default", required=False, help="default answer when cancelled"
)

subparsers = parser.add_subparsers(title="prompt type", required=True)

from . import list, input, confirm, checkbox


def main():
    result = parser.parse_args()
    result = vars(result)
    prompt: Callable[..., None] = result.pop("func")
    prompt(**result)

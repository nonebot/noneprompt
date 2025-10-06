from argparse import ArgumentParser
from typing import Callable

parser = ArgumentParser(prog="noneprompt", description="A simple prompt toolkit.")
parser.add_argument(
    "--no-ansi", action="store_true", required=False, help="disable ANSI colors"
)
parser.add_argument(
    "-d", "--default", required=False, help="default answer when cancelled"
)

subparsers = parser.add_subparsers(title="prompt type", required=True)

from . import checkbox as _checkbox  # noqa: F401
from . import confirm as _confirm  # noqa: F401
from . import input as _input  # noqa: F401
from . import list as _list  # noqa: F401


def main():
    result = parser.parse_args()
    result = vars(result)
    prompt: Callable[..., None] = result.pop("func")
    prompt(**result)

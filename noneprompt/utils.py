from typing import Optional

from prompt_toolkit.styles import Style

BOOLEAN_STRING_TRUE = {"yes", "y", "true", "t", "1"}
BOOLEAN_STRING_FALSE = {"no", "n", "false", "f", "0"}
BOOLEAN_STRING = BOOLEAN_STRING_TRUE | BOOLEAN_STRING_FALSE


def str2bool(value: str):
    return value.lower() in BOOLEAN_STRING_TRUE


def build_style(**kwargs: Optional[str]) -> Style:
    return Style([(k, v) for k, v in kwargs.items() if v is not None])

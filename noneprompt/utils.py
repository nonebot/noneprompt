from dataclasses import dataclass
from typing import Generic, TypeVar

RT = TypeVar("RT")


@dataclass
class Choice(Generic[RT]):
    """Choice item for sequence like prompts."""

    name: str
    data: RT = None  # type: ignore

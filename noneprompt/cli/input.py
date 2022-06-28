from typing import Optional

from noneprompt.utils import build_style
from noneprompt.prompts import InputPrompt

from . import subparsers
from ._options import (
    answer_style_option,
    question_mark_option,
    question_style_option,
    question_mark_style_option,
)


def input_prompt_main(
    question: str,
    default_text: Optional[str] = None,
    *,
    no_ansi: bool = False,
    default: Optional[str] = None,
    question_style: Optional[str] = None,
    question_mark: Optional[str] = None,
    question_mark_style: Optional[str] = None,
    answer_style: Optional[str] = None,
    **kwargs,
):
    prompt = InputPrompt(
        question, default_text=default_text, question_mark=question_mark
    )
    prompt.prompt(
        default=default,
        no_ansi=no_ansi,
        style=build_style(
            question=question_style,
            questionmark=question_mark_style,
            answer=answer_style,
        ),
    )


input_prompt = subparsers.add_parser(
    "input",
    description="Input prompt.",
    parents=[
        question_mark_option,
        question_mark_style_option,
        question_style_option,
        answer_style_option,
    ],
)
input_prompt.add_argument(
    "-d",
    "--default-text",
    required=False,
    help="default text",
)
input_prompt.add_argument("question", help="prompt question")
input_prompt.set_defaults(func=input_prompt_main)

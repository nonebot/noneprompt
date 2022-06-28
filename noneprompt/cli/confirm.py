from typing import Optional

from noneprompt.prompts import ConfirmPrompt
from noneprompt.utils import BOOLEAN_STRING, str2bool, build_style

from . import subparsers
from ._options import (
    answer_style_option,
    question_mark_option,
    question_style_option,
    annotation_style_option,
    question_mark_style_option,
)


def confirm_prompt_main(
    question: str,
    default_choice: Optional[bool] = None,
    *,
    no_ansi: bool = False,
    default: Optional[str] = None,
    question_style: Optional[str] = None,
    question_mark: Optional[str] = None,
    question_mark_style: Optional[str] = None,
    annotation_style: Optional[str] = None,
    answer_style: Optional[str] = None,
):
    prompt = ConfirmPrompt(
        question, default_choice=default_choice, question_mark=question_mark
    )
    prompt.prompt(
        default=default,
        no_ansi=no_ansi,
        style=build_style(
            question=question_style,
            questionmark=question_mark_style,
            annotation=annotation_style,
            answer=answer_style,
        ),
    )


confirm_prompt = subparsers.add_parser(
    "confirm",
    description="Confirm prompt.",
    parents=[
        question_mark_option,
        question_mark_style_option,
        question_style_option,
        annotation_style_option,
        answer_style_option,
    ],
)
confirm_prompt.add_argument(
    "-d",
    "--default-choice",
    type=str2bool,
    required=False,
    help="default choice",
)
confirm_prompt.add_argument("question", help="prompt question")
confirm_prompt.set_defaults(func=confirm_prompt_main)

from typing import List, Optional

from noneprompt.utils import build_style
from noneprompt.prompts import Choice, CheckboxPrompt

from . import subparsers
from ._options import (
    sign_option,
    unsign_option,
    pointer_option,
    annotation_option,
    sign_style_option,
    answer_style_option,
    select_style_option,
    unsign_style_option,
    pointer_style_option,
    question_mark_option,
    question_style_option,
    unselect_style_option,
    annotation_style_option,
    question_mark_style_option,
)


def checkbox_prompt_main(
    question: str,
    choices: List[str],
    *,
    no_ansi: bool = False,
    default: Optional[str] = None,
    question_style: Optional[str] = None,
    question_mark: Optional[str] = None,
    question_mark_style: Optional[str] = None,
    annotation: Optional[str] = None,
    annotation_style: Optional[str] = None,
    answer_style: Optional[str] = None,
    pointer: Optional[str] = None,
    pointer_style: Optional[str] = None,
    sign: Optional[str] = None,
    sign_style: Optional[str] = None,
    unsign: Optional[str] = None,
    unsign_style: Optional[str] = None,
    select_style: Optional[str] = None,
    unselect_style: Optional[str] = None,
    **kwargs,
):
    prompt = CheckboxPrompt(
        question,
        choices=[Choice(c) for c in choices],
        question_mark=question_mark,
        pointer=pointer,
        selected_sign=sign,
        unselected_sign=unsign,
        annotation=annotation,
    )
    prompt.prompt(
        default=default,
        no_ansi=no_ansi,
        style=build_style(
            question=question_style,
            questionmark=question_mark_style,
            annotation=annotation_style,
            answer=answer_style,
            pointer=pointer_style,
            sign=sign_style,
            unsign=unsign_style,
            selected=select_style,
            unselected=unselect_style,
        ),
    )


checkbox_prompt = subparsers.add_parser(
    "checkbox",
    description="Checkbox prompt.",
    parents=[
        question_mark_option,
        question_mark_style_option,
        question_style_option,
        annotation_option,
        annotation_style_option,
        answer_style_option,
        pointer_option,
        pointer_style_option,
        sign_option,
        sign_style_option,
        unsign_option,
        unsign_style_option,
        select_style_option,
        unselect_style_option,
    ],
)
checkbox_prompt.add_argument("question", help="prompt question")
checkbox_prompt.add_argument("choices", nargs="+", help="choices")
checkbox_prompt.set_defaults(func=checkbox_prompt_main)

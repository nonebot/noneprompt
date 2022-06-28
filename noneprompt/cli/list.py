from typing import List, Optional

from noneprompt.utils import build_style
from noneprompt.prompts import Choice, ListPrompt

from . import subparsers
from ._options import (
    pointer_option,
    annotation_option,
    answer_style_option,
    filter_style_option,
    select_style_option,
    pointer_style_option,
    question_mark_option,
    question_style_option,
    unselect_style_option,
    annotation_style_option,
    question_mark_style_option,
)


def list_prompt_main(
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
    filter_style: Optional[str] = None,
    answer_style: Optional[str] = None,
    pointer: Optional[str] = None,
    pointer_style: Optional[str] = None,
    select_style: Optional[str] = None,
    unselect_style: Optional[str] = None,
    **kwargs,
):
    prompt = ListPrompt(
        question,
        choices=[Choice(c) for c in choices],
        question_mark=question_mark,
        pointer=pointer,
        annotation=annotation,
    )
    prompt.prompt(
        default=default,
        no_ansi=no_ansi,
        style=build_style(
            question=question_style,
            questionmark=question_mark_style,
            annotation=annotation_style,
            filter=filter_style,
            answer=answer_style,
            pointer=pointer_style,
            selected=select_style,
            unselected=unselect_style,
        ),
    )


list_prompt = subparsers.add_parser(
    "list",
    description="List prompt.",
    parents=[
        question_mark_option,
        question_mark_style_option,
        question_style_option,
        annotation_option,
        annotation_style_option,
        filter_style_option,
        answer_style_option,
        pointer_option,
        pointer_style_option,
        select_style_option,
        unselect_style_option,
    ],
)
list_prompt.add_argument("question", help="prompt question")
list_prompt.add_argument("choices", nargs="+", help="choices")
list_prompt.set_defaults(func=list_prompt_main)

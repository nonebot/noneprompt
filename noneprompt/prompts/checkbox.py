from functools import partial
from gettext import gettext as _
import os
from typing import Callable, Optional, TypeVar

from prompt_toolkit.filters import Condition, is_done
from prompt_toolkit.formatted_text import AnyFormattedText
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import (
    ConditionalContainer,
    Float,
    FloatContainer,
    HSplit,
    Window,
)
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.mouse_events import MouseEvent, MouseEventType
from prompt_toolkit.styles import Style

from ._base import NO_ANSWER, BasePrompt
from ._choice import Choice

RT = TypeVar("RT")


class CheckboxPrompt(BasePrompt[tuple[Choice[RT], ...]]):
    """Checkbox Prompt that supports auto scrolling.

    Style class guide:

    ```
    [?] Choose a choice and return? (Use ↑ and ↓ to move, Space to select, Enter to submit)
    └┬┘ └──────────────┬──────────┘ └───────────────────────┬─────────────────────────────┘
    questionmark    question                            annotation

     ❯  ●  choice selected
    └┬┘└┬┘ └───────┬─────┘
    pointer sign selected

        ○  choice unselected
       └┬┘ └───────┬───────┘
      unsign   unselected
    ```
    """  # noqa: E501

    def __init__(
        self,
        question: str,
        choices: list[Choice[RT]],
        default_select: Optional[list[int]] = None,
        *,
        question_mark: Optional[str] = None,
        pointer: Optional[str] = None,
        selected_sign: Optional[str] = None,
        unselected_sign: Optional[str] = None,
        annotation: Optional[str] = None,
        max_height: Optional[int] = None,
        validator: Optional[Callable[[tuple[Choice[RT], ...]], bool]] = None,
        error_message: Optional[str] = None,
    ):
        self.question: str = question
        self.choices: list[Choice[RT]] = choices
        self.default_select: set[int] = (
            set()
            if default_select is None
            else {index % len(self.choices) for index in default_select}
        )
        self.question_mark: str = "[?]" if question_mark is None else question_mark
        self.pointer: str = "❯" if pointer is None else pointer
        self.selected_sign: str = "●" if selected_sign is None else selected_sign
        self.unselected_sign: str = "○" if unselected_sign is None else unselected_sign
        self.annotation: str = (
            _("(Use ↑ and ↓ to move, Space to select, Enter to submit)")
            if annotation is None
            else annotation
        )
        self.validator: Optional[Callable[[tuple[Choice[RT], ...]], bool]] = validator
        self.error_message: str = (
            _("Invalid selection") if error_message is None else error_message
        )

        self._index: int = 0
        self._display_index: int = 0
        self._max_height: Optional[int] = max_height

    @property
    def max_height(self) -> int:
        return self._max_height or os.get_terminal_size().lines

    def _reset(self):
        self._invalid: bool = False
        self._answered: bool = False
        self._selected: set[int] = self.default_select.copy()

    def _reset_error(self):
        self._invalid = False

    def _build_layout(self) -> Layout:
        self._reset()
        return Layout(
            FloatContainer(
                HSplit(
                    [
                        Window(
                            FormattedTextControl(self._get_prompt),
                            height=Dimension(1),
                            dont_extend_height=True,
                            always_hide_cursor=True,
                        ),
                        ConditionalContainer(
                            Window(
                                FormattedTextControl(self._get_choices_prompt),
                                height=Dimension(1),
                                dont_extend_height=True,
                                always_hide_cursor=True,
                            ),
                            ~is_done,
                        ),
                    ]
                ),
                [
                    Float(
                        ConditionalContainer(
                            Window(
                                FormattedTextControl(self._get_error_prompt),
                                height=1,
                                dont_extend_height=True,
                                always_hide_cursor=True,
                            ),
                            Condition(
                                lambda: bool(self.error_message and self._invalid)
                            )
                            & ~is_done,
                        ),
                        bottom=0,
                        left=0,
                    ),
                ],
            )
        )

    def _build_style(self, style: Style) -> Style:
        default = Style(
            [
                ("questionmark", "fg:#673AB7 bold"),
                ("question", "bold"),
                ("answer", "fg:#FF9D00"),
                ("annotation", "fg:#7F8C8D"),
                ("sign", "fg:ansigreen noreverse"),
                ("selected", "fg:ansigreen noreverse"),
                ("error", "bg:#FF0000"),
            ]
        )
        return Style([*default.style_rules, *style.style_rules])

    def _build_keybindings(self) -> KeyBindings:
        kb = KeyBindings()

        @kb.add("up", eager=True)
        def previous(event: KeyPressEvent):
            self._reset_error()
            self._handle_up()

        @kb.add("down", eager=True)
        def next(event: KeyPressEvent):
            self._reset_error()
            self._handle_down()

        @kb.add("space", eager=True)
        def select(event: KeyPressEvent):
            self._reset_error()
            if self._index not in self._selected:
                self._selected.add(self._index)
            else:
                self._selected.remove(self._index)

        @kb.add("enter", eager=True)
        def enter(event: KeyPressEvent):
            self._reset_error()
            if self.validator is not None:
                self._invalid = not self.validator(self._get_result())
                if self._invalid:
                    return

            self._answered = True
            event.app.exit(result=self._get_result())

        @kb.add("c-c", eager=True)
        @kb.add("c-q", eager=True)
        def quit(event: KeyPressEvent):
            self._reset_error()
            event.app.exit(result=NO_ANSWER)

        return kb

    def _get_prompt(self) -> AnyFormattedText:
        prompts: AnyFormattedText = []
        if self.question_mark:
            prompts.append(("class:questionmark", self.question_mark))
            prompts.append(("", " "))
        prompts.append(("class:question", self.question.strip()))
        prompts.append(("", " "))
        if self._answered:
            result = self._get_result()
            prompts.append(
                (
                    "class:answer",
                    ", ".join(choice.name.strip() for choice in result),
                )
            )
        else:
            prompts.append(("class:annotation", self.annotation))
        return prompts

    def _get_choices_prompt(self) -> AnyFormattedText:
        max_num = self.max_height - 1

        prompts: AnyFormattedText = []
        for index, choice in enumerate(
            self.choices[self._display_index : self._display_index + max_num]
        ):
            current_index = index + self._display_index

            # pointer
            if current_index == self._index:
                prompts.append(
                    (
                        "class:pointer",
                        self.pointer,
                        self._get_mouse_handler(current_index),
                    )
                )
            else:
                prompts.append(
                    (
                        "",
                        " " * len(self.pointer),
                        self._get_mouse_handler(current_index),
                    )
                )

            # space
            prompts.append(("", " ", self._get_mouse_handler(current_index)))

            # sign and text
            if current_index in self._selected:
                prompts.append(
                    (
                        "class:sign",
                        self.selected_sign,
                        self._get_mouse_handler(current_index),
                    )
                )
                prompts.append(("", " ", self._get_mouse_handler(current_index)))
                prompts.append(
                    (
                        "class:selected",
                        choice.name.strip() + "\n",
                        self._get_mouse_handler(current_index),
                    )
                )
            else:
                prompts.append(
                    (
                        "class:unsign",
                        self.unselected_sign,
                        self._get_mouse_handler(current_index),
                    )
                )
                prompts.append(("", " ", self._get_mouse_handler(current_index)))
                prompts.append(
                    (
                        "class:unselected",
                        choice.name.strip() + "\n",
                        self._get_mouse_handler(current_index),
                    )
                )
        return prompts

    def _get_error_prompt(self) -> AnyFormattedText:
        return [("class:error", self.error_message, lambda e: self._reset_error())]

    def _get_result(self) -> tuple[Choice[RT], ...]:
        return tuple(
            choice
            for index, choice in enumerate(self.choices)
            if index in self._selected
        )

    def _get_mouse_handler(
        self, index: Optional[int] = None
    ) -> Callable[[MouseEvent], None]:
        return partial(self._handle_mouse, index=index)

    def _handle_mouse(self, event: MouseEvent, index: Optional[int] = None) -> None:
        self._reset_error()
        if event.event_type == MouseEventType.MOUSE_UP and index is not None:
            self._jump_to(index)
            if self._index not in self._selected:
                self._selected.add(self._index)
            else:
                self._selected.remove(self._index)
        elif event.event_type == MouseEventType.SCROLL_UP:
            self._handle_up()
        elif event.event_type == MouseEventType.SCROLL_DOWN:
            self._handle_down()

    def _handle_up(self) -> None:
        self._jump_to((self._index - 1) % len(self.choices))

    def _handle_down(self) -> None:
        self._jump_to((self._index + 1) % len(self.choices))

    def _jump_to(self, index: int) -> None:
        self._index = index
        end_index = self._display_index + self.max_height - 2
        if self._index == self._display_index and self._display_index > 0:
            self._display_index -= 1
        elif self._index == len(self.choices) - 1:
            start_index = len(self.choices) - self.max_height + 1
            self._display_index = max(start_index, 0)
        elif self._index == end_index and end_index < len(self.choices) - 1:
            self._display_index += 1
        elif self._index == 0:
            self._display_index = 0

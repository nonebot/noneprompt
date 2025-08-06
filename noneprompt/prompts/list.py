import os
from time import time
from functools import lru_cache
from gettext import gettext as _
from typing import List, TypeVar, Callable, Optional

from prompt_toolkit.styles import Style
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout import Layout
from prompt_toolkit.lexers import SimpleLexer
from prompt_toolkit.application import get_app
from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.filters import Condition, is_done
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.formatted_text import AnyFormattedText
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent
from prompt_toolkit.mouse_events import MouseEvent, MouseEventType
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.containers import (
    Float,
    HSplit,
    Window,
    FloatContainer,
    ConditionalContainer,
)

from ._choice import Choice
from ._base import NO_ANSWER, BasePrompt

RT = TypeVar("RT")


class ListPrompt(BasePrompt[Choice[RT]]):
    """RadioList Prompt that supports auto scrolling.

    Style class guide:

    ```
    [?] Choose a choice and return? (Use ↑ and ↓ to choose, Enter to submit) input
    └┬┘ └──────────────┬──────────┘ └────────────────────┬─────────────────┘ └─┬─┘
    questionmark    question                         annotation              filter

     ❯  choice selected
    └┬┘ └───────┬─────┘
    pointer  selected

        choice unselected
        └───────┬───────┘
            unselected

    Invalid input
    └─────┬─────┘
        error
    ```
    """

    def __init__(
        self,
        question: str,
        choices: List[Choice[RT]],
        allow_filter: bool = True,
        default_select: Optional[int] = None,
        *,
        question_mark: Optional[str] = None,
        pointer: Optional[str] = None,
        annotation: Optional[str] = None,
        max_height: Optional[int] = None,
        custom_filter: Optional[Callable[[str, Choice[RT]], bool]] = None,
        validator: Optional[Callable[[Choice[RT]], bool]] = None,
        error_message: Optional[str] = None,
    ):
        self.question: str = question
        self.choices: List[Choice[RT]] = choices
        self.allow_filter: bool = allow_filter
        self.question_mark: str = "[?]" if question_mark is None else question_mark
        self.pointer: str = "❯" if pointer is None else pointer
        self.annotation: str = (
            _("(Use ↑ and ↓ to choose, Enter to submit)")
            if annotation is None
            else annotation
        )
        self.filter: Callable[[str, Choice[RT]], bool] = custom_filter or (
            lambda text, choice: text.lower() in choice.name.lower()
        )
        self.validator: Optional[Callable[[Choice[RT]], bool]] = validator
        self.error_message: str = (
            _("Invalid selection") if error_message is None else error_message
        )

        self._index: int = (default_select or 0) % len(self.choices)
        self._display_index: int = 0
        self._max_height: Optional[int] = max_height

        self._last_mouse_up: float = 0
        self._last_mouse_index: int = 0

    @property
    def max_height(self) -> int:
        return self._max_height or os.get_terminal_size().lines

    @property
    def filtered_choices(self) -> List[Choice[RT]]:
        return [
            choice for choice in self.choices if self.filter(self._buffer.text, choice)
        ]

    def _reset(self):
        self._invalid: bool = False
        self._answered: Optional[Choice] = None
        self._reset_choice_layout()
        self._buffer: Buffer = Buffer(
            name=DEFAULT_BUFFER,
            multiline=False,
            on_text_changed=lambda b: self._reset_choice_layout(),
        )

    def _reset_choice_layout(self):
        self._index: int = 0
        self._display_index: int = 0
        self._reset_error()

    def _reset_error(self):
        self._invalid = False

    def _build_layout(self) -> Layout:
        self._reset()
        if self.allow_filter:
            prompt_line = Window(
                BufferControl(
                    self._buffer,
                    lexer=SimpleLexer("class:filter"),
                    focus_on_click=~is_done,
                ),
                dont_extend_height=True,
                get_line_prefix=self._get_line_prefix,
            )
        else:
            prompt_line = Window(
                FormattedTextControl(self._get_prompt),
                height=Dimension(1),
                dont_extend_height=True,
                always_hide_cursor=True,
            )

        return Layout(
            FloatContainer(
                HSplit(
                    [
                        prompt_line,
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
                                lambda: self.error_message is not None and self._invalid
                            )
                            & ~is_done,
                        ),
                        bottom=0,
                        left=0,
                    )
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

        @kb.add("enter", eager=True)
        def enter(event: KeyPressEvent):
            self._reset_error()
            self._finish()

        @kb.add("c-c", eager=True)
        @kb.add("c-q", eager=True)
        def quit(event: KeyPressEvent):
            self._reset_error()
            event.app.exit(result=NO_ANSWER)

        return kb

    def _finish(self) -> None:
        # no answer selected
        if not self.filtered_choices:
            return

        # get result first
        result = self.filtered_choices[self._index]
        # validate result
        if self.validator is not None:
            self._invalid = not self.validator(result)
            if self._invalid:
                return

        self._answered = result
        # then clear buffer
        self._buffer.reset()
        get_app().exit(result=result)

    def _get_line_prefix(self, line_number: int, wrap_count: int) -> AnyFormattedText:
        return self._get_prompt()

    def _get_prompt(self) -> AnyFormattedText:
        prompts: AnyFormattedText = []
        if self.question_mark:
            prompts.append(("class:questionmark", self.question_mark))
            prompts.append(("", " "))
        prompts.append(("class:question", self.question.strip()))
        prompts.append(("", " "))
        if self._answered:
            prompts.append(("class:answer", self._answered.name.strip()))
        else:
            prompts.append(("class:annotation", self.annotation))
            prompts.append(("", " "))
        return prompts

    def _get_choices_prompt(self) -> AnyFormattedText:
        max_num = self.max_height - 1

        prompts: AnyFormattedText = []
        for index, choice in enumerate(
            self.filtered_choices[self._display_index : self._display_index + max_num]
        ):
            current_index = index + self._display_index
            if current_index == self._index:
                prompts.append(
                    (
                        "class:pointer",
                        self.pointer,
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
                        "",
                        " " * len(self.pointer),
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

    @lru_cache
    def _get_mouse_handler(
        self, index: Optional[int] = None
    ) -> Callable[[MouseEvent], None]:
        def _handle_mouse(event: MouseEvent) -> None:
            self._reset_error()
            if event.event_type == MouseEventType.MOUSE_UP and index is not None:
                self._jump_to(index)
                if (
                    time() - self._last_mouse_up
                ) < 0.3 and index == self._last_mouse_index:
                    self._finish()
                else:
                    self._last_mouse_up = time()
                    self._last_mouse_index = index
            elif event.event_type == MouseEventType.SCROLL_UP:
                self._handle_up()
            elif event.event_type == MouseEventType.SCROLL_DOWN:
                self._handle_down()

        return _handle_mouse

    def _handle_up(self) -> None:
        if self.filtered_choices:
            self._jump_to((self._index - 1) % len(self.filtered_choices))

    def _handle_down(self) -> None:
        if self.filtered_choices:
            self._jump_to((self._index + 1) % len(self.filtered_choices))

    def _jump_to(self, index: int) -> None:
        self._index = index
        choice_num = len(self.filtered_choices)
        end_index = self._display_index + self.max_height - 2
        if self._index == self._display_index and self._display_index > 0:
            self._display_index -= 1
        elif self._index == choice_num - 1:
            start_index = choice_num - self.max_height + 1
            self._display_index = max(start_index, 0)
        elif self._index == end_index and end_index < choice_num - 1:
            self._display_index += 1
        elif self._index == 0:
            self._display_index = 0

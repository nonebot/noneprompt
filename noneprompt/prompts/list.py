import os
from functools import lru_cache
from typing import List, TypeVar, Callable, Optional

from prompt_toolkit.styles import Style
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout import Layout
from prompt_toolkit.filters import is_done
from prompt_toolkit.lexers import SimpleLexer
from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.formatted_text import AnyFormattedText
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent
from prompt_toolkit.mouse_events import MouseEvent, MouseEventType
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.containers import HSplit, Window, ConditionalContainer

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
    ```
    """

    def __init__(
        self,
        question: str,
        choices: List[Choice[RT]],
        allow_filter: bool = True,
        *,
        question_mark: Optional[str] = None,
        pointer: Optional[str] = None,
        annotation: Optional[str] = None,
        max_height: Optional[int] = None,
    ):
        self.question: str = question
        self.choices: List[Choice[RT]] = choices
        self.allow_filter: bool = allow_filter
        self.question_mark: str = "[?]" if question_mark is None else question_mark
        self.pointer: str = "❯" if pointer is None else pointer
        self.annotation: str = (
            "(Use ↑ and ↓ to choose, Enter to submit)"
            if annotation is None
            else annotation
        )
        self._index: int = 0
        self._display_index: int = 0
        self._max_height: Optional[int] = max_height

    @property
    def max_height(self) -> int:
        return self._max_height or os.get_terminal_size().lines

    @property
    def filtered_choices(self) -> List[Choice[RT]]:
        return [choice for choice in self.choices if self._buffer.text in choice.name]

    def _reset(self):
        self._answered: Optional[Choice] = None
        self._buffer: Buffer = Buffer(
            name=DEFAULT_BUFFER,
            multiline=False,
            on_text_changed=self._reset_choice_layout,
        )

    def _reset_choice_layout(self, buffer: Buffer):
        self._index: int = 0
        self._display_index: int = 0

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
            )
        )

    def _build_style(self, style: Style) -> Style:
        default = Style(
            [
                ("questionmark", "fg:#5F819D"),
                ("question", "bold"),
                ("answer", "fg:#FF9D00"),
                ("annotation", "fg:#7F8C8D"),
                ("selected", "fg:ansigreen noreverse"),
            ]
        )
        return Style([*default.style_rules, *style.style_rules])

    def _build_keybindings(self) -> KeyBindings:
        kb = KeyBindings()

        @kb.add("up", eager=True)
        def previous(event: KeyPressEvent):
            self._handle_up()

        @kb.add("down", eager=True)
        def next(event: KeyPressEvent):
            self._handle_down()

        @kb.add("enter", eager=True)
        def enter(event: KeyPressEvent):
            # no answer selected
            if not self.filtered_choices:
                return

            # get result first
            result = self.filtered_choices[self._index]
            self._answered = result
            # then clear buffer
            self._buffer.reset()
            event.app.exit(result=result)

        @kb.add("c-c", eager=True)
        @kb.add("c-q", eager=True)
        def quit(event: KeyPressEvent):
            event.app.exit(result=NO_ANSWER)

        return kb

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

    @lru_cache
    def _get_mouse_handler(
        self, index: Optional[int] = None
    ) -> Callable[[MouseEvent], None]:
        def _handle_mouse(event: MouseEvent) -> None:
            if event.event_type == MouseEventType.MOUSE_UP and index is not None:
                self._jump_to(index)
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

import os
from functools import lru_cache
from typing import Set, List, Tuple, TypeVar, Callable, Optional

from prompt_toolkit.styles import Style
from prompt_toolkit.layout import Layout
from prompt_toolkit.filters import is_done
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.formatted_text import AnyFormattedText
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent
from prompt_toolkit.mouse_events import MouseEvent, MouseEventType
from prompt_toolkit.layout.containers import HSplit, Window, ConditionalContainer

from ._choice import Choice
from ._base import NO_ANSWER, BasePrompt

RT = TypeVar("RT")


class CheckboxPrompt(BasePrompt[Tuple[Choice[RT], ...]]):
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
    """

    def __init__(
        self,
        question: str,
        choices: List[Choice[RT]],
        default_select: Optional[List[int]] = None,
        *,
        question_mark: Optional[str] = None,
        pointer: Optional[str] = None,
        selected_sign: Optional[str] = None,
        unselected_sign: Optional[str] = None,
        annotation: Optional[str] = None,
        max_height: Optional[int] = None,
        validator: Optional[Callable[[Tuple[Choice[RT], ...]], bool]] = None,
    ):
        self.question: str = question
        self.choices: List[Choice[RT]] = choices
        self.default_select: Set[int] = (
            set()
            if default_select is None
            else set(index % len(self.choices) for index in default_select)
        )
        self.question_mark: str = "[?]" if question_mark is None else question_mark
        self.pointer: str = "❯" if pointer is None else pointer
        self.selected_sign: str = "●" if selected_sign is None else selected_sign
        self.unselected_sign: str = "○" if unselected_sign is None else unselected_sign
        self.annotation: str = (
            "(Use ↑ and ↓ to move, Space to select, Enter to submit)"
            if annotation is None
            else annotation
        )
        self.validator: Optional[Callable[[Tuple[Choice[RT], ...]], bool]] = validator
        self._index: int = 0
        self._display_index: int = 0
        self._max_height: Optional[int] = max_height

    @property
    def max_height(self) -> int:
        return self._max_height or os.get_terminal_size().lines

    def _reset(self):
        self._answered: bool = False
        self._selected: Set[int] = self.default_select.copy()

    def _build_layout(self) -> Layout:
        self._reset()
        return Layout(
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

        @kb.add("space", eager=True)
        def select(event: KeyPressEvent):
            if self._index not in self._selected:
                self._selected.add(self._index)
            else:
                self._selected.remove(self._index)

        @kb.add("enter", eager=True)
        def enter(event: KeyPressEvent):
            if self.validator and not self.validator(self._get_result()):
                return
            self._answered = True
            event.app.exit(result=self._get_result())

        @kb.add("c-c", eager=True)
        @kb.add("c-q", eager=True)
        def quit(event: KeyPressEvent):
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

    def _get_result(self) -> Tuple[Choice[RT], ...]:
        return tuple(
            choice
            for index, choice in enumerate(self.choices)
            if index in self._selected
        )

    @lru_cache
    def _get_mouse_handler(
        self, index: Optional[int] = None
    ) -> Callable[[MouseEvent], None]:
        def _handle_mouse(event: MouseEvent) -> None:
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

        return _handle_mouse

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

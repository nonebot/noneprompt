from typing import Callable, Optional

from prompt_toolkit.styles import Style
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout import Layout
from prompt_toolkit.lexers import SimpleLexer
from prompt_toolkit.application import get_app
from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.validation import Validator
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.formatted_text import AnyFormattedText
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent

from ._base import NO_ANSWER, BasePrompt


class InputPrompt(BasePrompt[str]):
    """Simple Input Prompt.

    Style class guide:

    ```
    [?] Choose a choice and return? answer
    └┬┘ └──────────────┬──────────┘ └──┬─┘
    questionmark    question        answer
    ```
    """

    def __init__(
        self,
        question: str,
        default_text: Optional[str] = None,
        *,
        question_mark: Optional[str] = None,
        validator: Optional[Callable[[str], bool]] = None,
    ):
        self.question: str = question
        self.default_text: Optional[str] = default_text
        self.question_mark: str = "[?]" if question_mark is None else question_mark
        self.validator: Optional[Callable[[str], bool]] = validator

    def _reset(self):
        self._answered: bool = False
        self._buffer: Buffer = Buffer(
            name=DEFAULT_BUFFER,
            validator=self.validator and Validator.from_callable(self.validator),
            accept_handler=self._submit,
            multiline=False,
        )
        if self.default_text:
            self._buffer.insert_text(self.default_text)

    def _build_layout(self) -> Layout:
        self._reset()
        return Layout(
            HSplit(
                [
                    Window(
                        BufferControl(self._buffer, lexer=SimpleLexer("class:answer")),
                        dont_extend_height=True,
                        get_line_prefix=self._get_prompt,
                    )
                ]
            )
        )

    def _build_style(self, style: Style) -> Style:
        default = Style(
            [
                ("questionmark", "fg:#5F819D"),
                ("question", "bold"),
                ("answer", "fg:#5F819D"),
            ]
        )
        return Style([*default.style_rules, *style.style_rules])

    def _build_keybindings(self) -> KeyBindings:
        kb = KeyBindings()

        @kb.add("enter", eager=True)
        def enter(event: KeyPressEvent):
            self._buffer.validate_and_handle()

        @kb.add("c-c", eager=True)
        @kb.add("c-q", eager=True)
        def quit(event: KeyPressEvent):
            event.app.exit(result=NO_ANSWER)

        return kb

    def _get_prompt(self, line_number: int, wrap_count: int) -> AnyFormattedText:
        prompts: AnyFormattedText = []
        if self.question_mark:
            prompts.append(("class:questionmark", self.question_mark))
            prompts.append(("", " "))
        prompts.append(("class:question", self.question.strip()))
        prompts.append(("", " "))
        return prompts

    def _submit(self, buffer: Buffer) -> bool:
        self._answered = True
        get_app().exit(result=buffer.document.text)
        return True

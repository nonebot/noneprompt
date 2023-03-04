from gettext import gettext as _
from typing import Union, Callable, Optional

from prompt_toolkit.styles import Style
from prompt_toolkit.layout import Layout
from prompt_toolkit.application import get_app
from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.validation import Validator
from prompt_toolkit.buffer import Buffer, ValidationState
from prompt_toolkit.formatted_text import AnyFormattedText
from prompt_toolkit.lexers import SimpleLexer, DynamicLexer
from prompt_toolkit.filters import Filter, Condition, is_done
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.containers import HSplit, Window, ConditionalContainer
from prompt_toolkit.layout.processors import PasswordProcessor, ConditionalProcessor

from ._base import NO_ANSWER, BasePrompt


class InputPrompt(BasePrompt[str]):
    """Simple Input Prompt.

    Style class guide:

    ```
    [?] Choose a choice and return? answer
    └┬┘ └──────────────┬──────────┘ └──┬─┘
    questionmark    question      input/answer

    Invalid input
    └─────┬─────┘
        error
    ```
    """

    def __init__(
        self,
        question: str,
        default_text: Optional[str] = None,
        is_password: Union[bool, Filter] = False,
        *,
        question_mark: Optional[str] = None,
        validator: Optional[Callable[[str], bool]] = None,
        error_message: Optional[str] = None,
    ):
        self.question: str = question
        self.default_text: Optional[str] = default_text
        self.is_password: Union[bool, Filter] = is_password
        self.question_mark: str = "[?]" if question_mark is None else question_mark
        self.validator: Optional[Callable[[str], bool]] = validator
        self.error_message: str = (
            _("Invalid input") if error_message is None else error_message
        )

    def _reset(self):
        self._answered: bool = False
        self._invalid: bool = False
        self._buffer: Buffer = Buffer(
            name=DEFAULT_BUFFER,
            validator=self.validator
            and Validator.from_callable(self.validator, move_cursor_to_end=True),
            accept_handler=self._submit,
            multiline=False,
            on_text_changed=self._on_text_changed,
        )
        if self.default_text:
            self._buffer.insert_text(self.default_text)

    def _reset_error(self):
        self._invalid = False

    def _build_layout(self) -> Layout:
        self._reset()
        return Layout(
            HSplit(
                [
                    Window(
                        BufferControl(
                            self._buffer,
                            input_processors=[
                                ConditionalProcessor(
                                    PasswordProcessor(), self.is_password
                                )
                            ],
                            lexer=DynamicLexer(
                                lambda: (
                                    SimpleLexer("class:answer")
                                    if self._answered
                                    else SimpleLexer("class:input")
                                )
                            ),
                        ),
                        dont_extend_height=True,
                        get_line_prefix=self._get_prompt,
                    ),
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
                ]
            )
        )

    def _build_style(self, style: Style) -> Style:
        default = Style(
            [
                ("questionmark", "fg:#673AB7 bold"),
                ("question", "bold"),
                ("answer", "fg:#FF9D00"),
                ("error", "bg:#FF0000"),
            ]
        )
        return Style([*default.style_rules, *style.style_rules])

    def _build_keybindings(self) -> KeyBindings:
        kb = KeyBindings()

        @kb.add("enter", eager=True)
        def enter(event: KeyPressEvent):
            self._buffer.validate_and_handle()
            if self._buffer.validation_state == ValidationState.INVALID:
                self._invalid = True

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

    def _get_error_prompt(self) -> AnyFormattedText:
        return [("class:error", self.error_message, lambda e: self._reset_error())]

    def _submit(self, buffer: Buffer) -> bool:
        self._answered = True
        get_app().exit(result=buffer.document.text)
        return True

    def _on_text_changed(self, buffer: Buffer) -> None:
        self._reset_error()

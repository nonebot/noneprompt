import abc
from gettext import gettext as _
from typing import Union, Generic, TypeVar, Optional, overload

from prompt_toolkit.layout import Layout
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Attrs, Style, StyleTransformation

DT = TypeVar("DT")
RT = TypeVar("RT")


NO_ANSWER = ...


class UndefinedType:
    def __str__(self):
        return "Undefined"

    def __bool__(self):
        return False


UNDEFINED = UndefinedType()


class CancelledError(Exception):
    """User cancelled answer."""


class DisableColorTransformation(StyleTransformation):
    def __init__(self, no_ansi: bool = False):
        self.no_ansi = no_ansi

    def transform_attrs(self, attrs: Attrs) -> Attrs:
        if self.no_ansi:
            return Attrs("", "", False, False, False, False, False, False, False)
        return attrs


class BasePrompt(abc.ABC, Generic[RT]):
    @abc.abstractmethod
    def _build_layout(self) -> Layout:
        raise NotImplementedError

    @abc.abstractmethod
    def _build_style(self, style: Style) -> Style:
        raise NotImplementedError

    @abc.abstractmethod
    def _build_keybindings(self) -> KeyBindings:
        raise NotImplementedError

    def _build_application(self, no_ansi: bool, style: Style) -> Application:
        return Application(
            layout=self._build_layout(),
            style=self._build_style(style),
            style_transformation=DisableColorTransformation(no_ansi),
            key_bindings=self._build_keybindings(),
            mouse_support=True,
        )

    @overload
    def prompt(
        self,
        default: UndefinedType = UNDEFINED,
        no_ansi: bool = False,
        style: Optional[Style] = None,
    ) -> RT: ...

    @overload
    def prompt(
        self,
        default: DT,
        no_ansi: bool = False,
        style: Optional[Style] = None,
    ) -> Union[DT, RT]: ...

    def prompt(
        self,
        default: Union[DT, UndefinedType] = UNDEFINED,
        no_ansi: bool = False,
        style: Optional[Style] = None,
    ) -> Union[DT, RT]:
        app = self._build_application(no_ansi=no_ansi, style=style or Style([]))
        result: RT = app.run()
        if result is not NO_ANSWER:
            return result
        if default is UNDEFINED:
            raise CancelledError(_("No answer selected!"))
        return default  # type: ignore

    @overload
    async def prompt_async(
        self,
        default: UndefinedType = UNDEFINED,
        no_ansi: bool = False,
        style: Optional[Style] = None,
    ) -> RT: ...

    @overload
    async def prompt_async(
        self,
        default: DT,
        no_ansi: bool = False,
        style: Optional[Style] = None,
    ) -> Union[DT, RT]: ...

    async def prompt_async(
        self,
        default: Union[DT, UndefinedType] = UNDEFINED,
        no_ansi: bool = False,
        style: Optional[Style] = None,
    ) -> Union[DT, RT]:
        app = self._build_application(no_ansi=no_ansi, style=style or Style([]))
        result: RT = await app.run_async()
        if result is not NO_ANSWER:
            return result
        if default is UNDEFINED:
            raise CancelledError(_("No answer selected!"))
        return default  # type: ignore

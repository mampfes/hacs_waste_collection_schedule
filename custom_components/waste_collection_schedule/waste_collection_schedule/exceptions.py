"""Source exceptions backed by the i18n phrase registry.

Each subclass stores a ``phrase_key`` plus the placeholder values needed to
format that phrase. ``.message`` resolves lazily, defaulting to English so
``str(exc)`` and existing log output continue to behave the same way.
Display layers (config_flow, sensor) can re-render the message in the
user's Home Assistant UI language by calling ``exc.render(lang)``.

The ``__init__`` signatures are unchanged from the previous hand-built
English implementation, so all existing ``raise SourceArgumentNotFound(...)``
call sites continue to work without modification — the change is internal.
"""

from __future__ import annotations

from typing import Any, Generic, Iterable, Type, TypeVar

from .i18n_runtime import phrase

T = TypeVar("T")


class SourceArgumentExceptionMultiple(Exception):
    """Error base class for errors associated with multiple arguments."""

    def __init__(self, arguments: Iterable[str], message: str) -> None:
        self._arguments = list(arguments)
        self.phrase_key: str | None = None
        self.placeholders: dict[str, Any] = {}
        self.message = message
        super().__init__(self.message)

    @property
    def arguments(self) -> Iterable[str]:
        return self._arguments

    def render(self, lang: str = "en") -> str:
        if self.phrase_key is None:
            return self.message
        return phrase(self.phrase_key, lang=lang, **self.placeholders)


class SourceArgumentException(Exception):
    """Base for exceptions tied to a single source argument.

    Subclasses set ``phrase_key`` and ``placeholders`` to drive both the
    English ``.message`` rendering and any later locale resolution.
    """

    def __init__(
        self,
        argument: str,
        message: str | None = None,
        *,
        phrase_key: str | None = None,
        placeholders: dict[str, Any] | None = None,
    ) -> None:
        self._argument = argument
        self.phrase_key = phrase_key
        self.placeholders: dict[str, Any] = dict(placeholders or {})
        if message is None and phrase_key is not None:
            message = phrase(phrase_key, lang="en", **self.placeholders)
        self.message = message or ""
        super().__init__(self.message)

    @property
    def argument(self) -> str:
        return self._argument

    def render(self, lang: str = "en") -> str:
        """Render the message in ``lang`` (falls back to English)."""
        if self.phrase_key is None:
            return self.message
        return phrase(self.phrase_key, lang=lang, **self.placeholders)


class SourceArgumentSuggestionsExceptionBase(SourceArgumentException, Generic[T]):
    """Base for exceptions that carry a suggestions list."""

    def __init__(
        self,
        argument: str,
        suggestions: Iterable[T],
        *,
        phrase_key: str,
        placeholders: dict[str, Any],
    ) -> None:
        self._suggestions = list(suggestions)
        self._suggestion_type: Type[T] | None = (
            type(self._suggestions[0]) if self._suggestions else None
        )
        super().__init__(
            argument=argument, phrase_key=phrase_key, placeholders=placeholders
        )

    @property
    def suggestions(self) -> Iterable[T]:
        return self._suggestions

    @property
    def suggestion_type(self) -> Type[T] | None:
        return self._suggestion_type

    @property
    def simple_message(self) -> str:
        """The message without the suggestion list — kept for callers
        that previously relied on the bare-bones text.
        """
        return phrase(
            self.phrase_key.replace("_with_suggestions", "").replace(
                "_no_suggestions", ""
            )
            + ("_check_spelling" if "_not_found" in (self.phrase_key or "") else ""),
            lang="en",
            **self.placeholders,
        )


class SourceArgumentNotFound(SourceArgumentException):
    """Source argument value didn't match any candidate."""

    def __init__(
        self,
        argument: str,
        value: Any,
        message_addition: str = "please check the spelling and try again.",
    ) -> None:
        if message_addition == "please check the spelling and try again.":
            phrase_key = "errors.argument_not_found_check_spelling"
        else:
            phrase_key = "errors.argument_not_found"
        placeholders = {"argument": argument, "value": value}
        super().__init__(
            argument=argument, phrase_key=phrase_key, placeholders=placeholders
        )
        # Preserve free-text addition for callers using legacy phrasing.
        if message_addition and message_addition != "please check the spelling and try again.":
            self.message = (
                phrase("errors.argument_not_found", lang="en", **placeholders)
                + f" {message_addition}"
            )

    @property
    def simple_message(self) -> str:
        return phrase(
            "errors.argument_not_found", lang="en", **self.placeholders
        )


class SourceArgumentNotFoundWithSuggestions(SourceArgumentSuggestionsExceptionBase):
    """Source argument value didn't match; suggest alternatives."""

    def __init__(self, argument: str, value: Any, suggestions: Iterable[T]) -> None:
        suggestions_list = list(suggestions)
        if suggestions_list:
            phrase_key = "errors.argument_not_found_with_suggestions"
            placeholders = {
                "argument": argument,
                "value": value,
                "suggestions": suggestions_list,
            }
        else:
            phrase_key = "errors.argument_not_found_no_suggestions"
            placeholders = {"argument": argument, "value": value}
        super().__init__(
            argument=argument,
            suggestions=suggestions_list,
            phrase_key=phrase_key,
            placeholders=placeholders,
        )


class SourceArgAmbiguousWithSuggestions(SourceArgumentSuggestionsExceptionBase):
    """Multiple candidates matched; ask the user to pick one."""

    def __init__(self, argument: str, value: Any, suggestions: Iterable[T]) -> None:
        suggestions_list = list(suggestions)
        super().__init__(
            argument=argument,
            suggestions=suggestions_list,
            phrase_key="errors.argument_ambiguous",
            placeholders={
                "argument": argument,
                "value": value,
                "suggestions": suggestions_list,
            },
        )


class SourceArgumentRequired(SourceArgumentException):
    """Argument is required but wasn't provided."""

    def __init__(self, argument: str, reason: str) -> None:
        if reason:
            phrase_key = "errors.argument_required_with_reason"
            placeholders = {"argument": argument, "reason": reason}
        else:
            phrase_key = "errors.argument_required"
            placeholders = {"argument": argument}
        super().__init__(
            argument=argument, phrase_key=phrase_key, placeholders=placeholders
        )


class SourceArgumentRequiredWithSuggestions(SourceArgumentSuggestionsExceptionBase):
    """Argument is required; suggest valid values."""

    def __init__(self, argument: str, reason: str, suggestions: Iterable[T]) -> None:
        suggestions_list = list(suggestions)
        if reason:
            phrase_key = "errors.argument_required_with_reason_and_suggestions"
            placeholders = {
                "argument": argument,
                "reason": reason,
                "suggestions": suggestions_list,
            }
        else:
            phrase_key = "errors.argument_required_with_suggestions"
            placeholders = {
                "argument": argument,
                "suggestions": suggestions_list,
            }
        super().__init__(
            argument=argument,
            suggestions=suggestions_list,
            phrase_key=phrase_key,
            placeholders=placeholders,
        )

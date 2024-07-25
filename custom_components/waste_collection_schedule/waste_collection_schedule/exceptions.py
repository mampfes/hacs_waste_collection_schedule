from typing import Any, Generic, Iterable, Type, TypeVar

T = TypeVar("T")


class SourceArgumentExceptionMultiple(Exception):
    def __init__(self, arguments: Iterable[str], message: str):
        self._arguments = arguments
        self.message = message
        super().__init__(self.message)

    @property
    def arguments(self) -> Iterable[str]:
        return self._arguments


class SourceArgumentException(Exception):
    def __init__(self, argument, message):
        self._argument = argument
        self.message = message
        super().__init__(self.message)

    @property
    def argument(self) -> str:
        return self._argument


class SourceArgumentSuggestionsExceptionBase(SourceArgumentException, Generic[T]):
    def __init__(
        self,
        argument: str,
        message: str,
        suggestions: Iterable[T],
        message_addition: str = "",
    ):
        self._simple_message = message
        message += f", {message_addition}" if message_addition else ""
        super().__init__(argument=argument, message=message)
        self._suggestions = suggestions
        self._suggestion_type: Type[T] | None = (
            type(list(suggestions)[0]) if suggestions else None
        )

    @property
    def suggestions(self) -> Iterable[T]:
        return self._suggestions

    @property
    def suggestion_type(self) -> Type[T] | None:
        return self._suggestion_type

    @property
    def simple_message(self) -> str:
        return self._simple_message


class SourceArgumentNotFound(SourceArgumentException):
    """Invalid arguments provided."""

    def __init__(
        self,
        argument: str,
        value: Any,
        message_addition="please check the spelling and try again.",
    ) -> None:
        self._simple_message = f"We could not find values for the argument '{argument}' with the value '{value}'"
        self.message = self._simple_message
        if message_addition:
            self.message += f", {message_addition}"
        super().__init__(argument, self.message)

    @property
    def simple_message(self) -> str:
        return self._simple_message


class SourceArgumentNotFoundWithSuggestions(SourceArgumentSuggestionsExceptionBase):
    def __init__(self, argument: str, value: Any, suggestions: Iterable[T]) -> None:
        message = f"We could not find values for the argument '{argument}' with the value '{value}'"
        suggestions = list(suggestions)
        if len(suggestions) == 0:
            message += ", We could not find any suggestions. Please also check other arguments."
            message_addition = ""
        else:
            message_addition = (
                f"you may want to use one of the following: {suggestions}"
            )
        super().__init__(
            argument=argument,
            message=message,
            message_addition=message_addition,
            suggestions=suggestions,
        )


class SourceArgAmbiguousWithSuggestions(SourceArgumentSuggestionsExceptionBase):
    def __init__(self, argument: str, value: Any, suggestions: Iterable[T]) -> None:
        message = f"Multiple values found for the argument '{argument}' with the value '{value}'"
        message_addition = f"please specify one of: {suggestions}"
        super().__init__(
            argument=argument,
            message=message,
            suggestions=suggestions,
            message_addition=message_addition,
        )


class SourceArgumentRequired(SourceArgumentException):
    """Argument must be provided."""

    def __init__(self, argument: str, reason: str) -> None:
        self.message = f"Argument '{argument}' must be provided"
        if reason:
            self.message += f", {reason}"
        super().__init__(argument, self.message)


class SourceArgumentRequiredWithSuggestions(SourceArgumentSuggestionsExceptionBase):
    """Argument must be provided."""

    def __init__(self, argument: str, reason: str, suggestions: Iterable[T]) -> None:
        message = f"Argument '{argument}' must be provided"
        message_addition = (
            f"you may want to use one of the following: {list(suggestions)}"
        )
        if reason:
            message += f", {reason}"
        super().__init__(
            argument=argument,
            message=message,
            message_addition=message_addition,
            suggestions=suggestions,
        )

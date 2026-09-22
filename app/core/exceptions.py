class UIBuilderError(Exception):
    """Base for all application errors."""


class ConfigurationError(UIBuilderError): ...


class LLMError(UIBuilderError): ...


class StructuredOutputError(LLMError):
    """LLM output failed schema validation."""


class ValidationError(UIBuilderError):
    """Semantic validation failed (unknown ID, invalid variant, bad nesting...)."""

    def __init__(self, message: str, *, target: str | None = None) -> None:
        super().__init__(message)
        self.target = target


class UnknownComponentError(ValidationError): ...


class UnknownRecipeError(ValidationError): ...


class UnknownTokenError(ValidationError): ...


class UnknownLayoutError(ValidationError): ...


class UnknownAnimationError(ValidationError): ...


class ResolutionError(UIBuilderError): ...


class RenderError(UIBuilderError):
    def __init__(self, message: str, *, stage: str, details: dict[str, object] | None = None):
        super().__init__(message)
        self.stage = stage
        self.details = details or {}


class IterationLimitExceeded(UIBuilderError): ...

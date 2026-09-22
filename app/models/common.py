from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class StrictModel(BaseModel):
    """All agent I/O models forbid unknown fields so LLM drift fails loudly."""

    model_config = ConfigDict(extra="forbid", frozen=False)


class Density(StrEnum):
    compact = "compact"
    comfortable = "comfortable"
    spacious = "spacious"


class Intensity(StrEnum):
    none = "none"
    subtle = "subtle"
    moderate = "moderate"
    expressive = "expressive"


class Breakpoint(StrEnum):
    mobile = "mobile"
    tablet = "tablet"
    desktop = "desktop"
    wide = "wide"


class Severity(StrEnum):
    critical = "critical"
    major = "major"
    minor = "minor"


class Dimension(StrEnum):
    layout = "layout"
    visual = "visual"
    ux = "ux"
    accessibility = "accessibility"

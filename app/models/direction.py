from pydantic import Field

from app.models.common import Density, StrictModel


class ScreenDirection(StrictModel):
    """Which recipe one planned screen is composed from."""

    screen_id: str
    recipe: str


class DesignDirection(StrictModel):
    visual_style: str
    theme: str
    density: Density = Density.comfortable
    typography: str
    radius: str
    #: Brand colour system; replaces the theme's colours. None keeps the theme's own.
    palette: str | None = None
    layout_strategy: str
    animation: str
    screens: list[ScreenDirection] = Field(min_length=1)

    def recipe_for(self, screen_id: str) -> str:
        for s in self.screens:
            if s.screen_id == screen_id:
                return s.recipe
        raise KeyError(f"no recipe chosen for screen '{screen_id}'")

from app.models.common import Density, StrictModel


class DesignDirection(StrictModel):
    visual_style: str
    theme: str
    density: Density = Density.comfortable
    typography: str
    radius: str
    layout_strategy: str
    animation: str
    recipe: str

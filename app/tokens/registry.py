from __future__ import annotations

from app.core.exceptions import UnknownTokenError, ValidationError
from app.core.registry import BaseRegistry
from app.tokens.models import Theme


class ThemeRegistry(BaseRegistry[Theme]):
    kind = "theme"
    not_found_error = UnknownTokenError

    def chain(self, theme_id: str) -> list[Theme]:
        """Root-first inheritance chain. Detects cycles."""
        seen: list[str] = []
        cur: str | None = theme_id
        out: list[Theme] = []
        while cur is not None:
            if cur in seen:
                raise ValidationError(
                    f"theme inheritance cycle: {' -> '.join([*seen, cur])}", target=theme_id
                )
            seen.append(cur)
            t = self.get(cur)
            out.append(t)
            cur = t.extends
        out.reverse()
        return out

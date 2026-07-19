from dataclasses import dataclass
from typing import Literal

ThemeMode = Literal["light", "dark"]

ThemeBase = Literal["slate", "gray", "zinc", "neutral", "stone", "pink"]

ThemePrimary = Literal[
    "blue",
    "azure",
    "indigo",
    "purple",
    "pink",
    "red",
    "orange",
    "yellow",
    "lime",
    "green",
    "teal",
    "cyan",
    "inverted",
]

ThemeRadius = float  # Valid values: 0, 0.5, 1, 1.5, 2.


@dataclass
class ThemeSettings:
    """Controls the Bootstrap theme attributes rendered on the `<html>` element.

    Example:
        ```python
        ThemeSettings(
            base="stone",
            primary="purple",
            radius=2,
            mode="light",
        )
        ```

        renders as:

        ```html
        <html data-bs-theme-base="stone"
              data-bs-theme-primary="purple"
              data-bs-theme-radius="2"
              data-bs-theme="light">
        ```

    Parameters:
        base: Neutral color palette used for backgrounds, borders, and text.
            `None` omits the `data-bs-theme-base` attribute, falling back to
            the CSS default.
        primary: Accent color used for links, buttons, and other interactive
            elements. `None` omits the `data-bs-theme-primary` attribute.
        radius: Corner rounding scale applied to buttons, cards, and inputs.
            `None` omits the `data-bs-theme-radius` attribute.
        mode: Color scheme rendered on the page, `"light"` or `"dark"`.
    """

    base: ThemeBase | None = "stone"
    primary: ThemePrimary | None = "azure"
    radius: ThemeRadius | None = 1
    mode: ThemeMode = "light"

    def html_attrs(self) -> dict[str, str]:
        """Build the `data-bs-theme-*` attribute dict for the `<html>` tag.

        Omits an attribute entirely when the corresponding field is `None`.
        """
        attrs: dict[str, str] = {"data-bs-theme": self.mode}
        if self.base is not None:
            attrs["data-bs-theme-base"] = self.base
        if self.primary is not None:
            attrs["data-bs-theme-primary"] = self.primary
        if self.radius is not None:
            attrs["data-bs-theme-radius"] = str(self.radius)
        return attrs

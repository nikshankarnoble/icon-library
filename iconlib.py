"""
Module for querying icons from the library, and generating Qt pixmap objects 
from them.

e.g
    >>> import iconlib
    >>> iconlib.get_path("material", "add", colour="white")
    '/path/to/iconlib/material/add_white.svg'
    >>> iconlib.get_qpixmap("material", "add", colour="white")
    <PySide2.QtGui.QPixmap object at 0x7f5c7b2c7a00>

"""

# Built-in
from pathlib import Path
from typing import Optional

# Third-party
from qtpy.QtGui import QColor, QPainter, QPixmap
from qtpy.QtCore import Qt
from qtpy.QtSvg import QSvgRenderer


# Path to the icon library
ICONLIB_ROOT = Path(__file__).parent / "icons"

LIBRARIES = {
    "material": {
        "path": "{icon}/{style}.{ext}",
        "defaults": {
            "style": "regular",
            "ext": "svg",
        },
    },
    "internal": {
        "path": "{icon}/{style}.{ext}",
        "defaults": {
            "style": "regular",
            "ext": "png",
        },
    },
}


def get_library_names() -> list[str]:
    """
    Returns a list of available icon libraries.

    Returns:
        list[str]: List of icon library names.
    """
    return sorted(list(LIBRARIES.keys()))


def get_path(library: str, icon: str, **kwargs) -> Path:
    """
    Resolve the path to the icon file.

    Args:
        library (str): The name of the library to search for the icon in.
        icon (str): The name of the icon.

    Raises:
        ValueError: If the specified library is not found.

    Returns:
        (Path): path on disk to the icon file.
    """
    library_config = LIBRARIES.get(library)
    if library_config is None:
        raise ValueError(
            f"Icon library {library} not found. Available libraries: "
            f"{get_library_names()}"
        )

    icon_path_template = library_config["path"]
    substitutions = library_config.get("defaults", {}).copy()
    substitutions.update({"icon": icon})
    substitutions.update(kwargs)
    relative_icon_path = icon_path_template.format(**substitutions)
    icon_path = ICONLIB_ROOT / library / relative_icon_path

    if not icon_path.exists():
        raise FileNotFoundError(f"No icon file found at: {icon_path}")

    return icon_path


def get_qpixmap(
    library: str,
    icon: str,
    width: int = 20,
    height: int = 20,
    colour: Optional[QColor] = None,
    **kwargs,
) -> QPixmap:
    """
    Return a QPixmap object for the specified icon, for use in a Qt application.

    Args:
        library (str):
            The name of the library to search for the icon in.
        icon (str):
            The name of the icon.
        width (int):
            The width of the created QPixmap. Defaults to 20.
        height (int):
            The height of the created QPixmap. Defaults to 20.
        colour (QColor | None):
            Applies a custom fill colour to the icon. For a PNG icon with
            transparency, the colour will be applied to any non-transparent
            pixels. For an SVG icon, the colour will be applied to the icon
            as a whole. If None, a PNG icon will be used as is, and an SVG icon
            will be rendered in white.

    Raises:
        ValueError: _description_

    Returns:
        (QPixmap): the icon as a QPixmap object.
    """
    icon_path = get_path(library, icon, **kwargs)
    if icon_path.suffix == ".svg":
        if not colour:
            colour = Qt.GlobalColor.white
        pixmap = _svg_to_pixmap(icon_path, width, height, colour)
    else:
        pixmap = QPixmap(icon_path)
        if colour:
            pixmap = _fill_pixmap_by_alpha(pixmap, colour)

    pixmap = pixmap.scaled(
        width,
        height,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    return pixmap


# Fill pixmap with provided colour, using transparency as matte
def _svg_to_pixmap(filepath: str, width: int, height: int, color: QColor) -> QPixmap:
    renderer = QSvgRenderer(str(filepath))
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)  # this is the destination, and only its alpha is used!
    painter.setCompositionMode(painter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(pixmap.rect(), color)
    painter.end()
    return pixmap


def _fill_pixmap_by_alpha(pixmap: QPixmap, fill_color: QColor) -> QPixmap:
    image = pixmap.toImage()
    width = image.width()
    height = image.height()

    for y in range(height):
        for x in range(width):
            pixel = image.pixelColor(x, y)
            if pixel.alpha() > 0:  # Non-transparent pixel
                fill_color.setAlpha(pixel.alpha())
                image.setPixelColor(x, y, fill_color)

    return QPixmap.fromImage(image)


if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication, QLabel, QMainWindow

    app = QApplication(sys.argv)
    win = QMainWindow()
    label = QLabel(win)
    label.setText("Hello, World!")
    label.setPixmap(get_qpixmap("material", "wifi_find", width=30, height=30))
    win.show()
    sys.exit(app.exec_())

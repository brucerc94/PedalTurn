from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path

import fitz


class PdfServiceError(RuntimeError):
    """Raised when a PDF cannot be opened or rendered."""


@dataclass(frozen=True)
class PageImage:
    width: int
    height: int
    pixels: bytes


class PdfService:
    def __init__(self, render_scale: float = 2.0, cache_size: int = 8):
        self._render_scale = render_scale
        self._cache_size = cache_size
        self._document: fitz.Document | None = None
        self._path: Path | None = None
        self._cache: OrderedDict[int, PageImage] = OrderedDict()

    @property
    def current_path(self) -> Path | None:
        return self._path

    @property
    def page_count(self) -> int:
        return len(self._document) if self._document else 0

    def open(self, path: Path) -> int:
        self.close()
        try:
            document = fitz.open(path)
        except Exception as exc:
            raise PdfServiceError(f"No se pudo abrir el PDF: {path}") from exc

        if document.needs_pass:
            document.close()
            raise PdfServiceError("El PDF está protegido con contraseña.")

        if len(document) == 0:
            document.close()
            raise PdfServiceError("El PDF no contiene páginas.")

        self._document = document
        self._path = path
        self._cache.clear()
        return len(document)

    def render_page(self, page_index: int) -> PageImage:
        if self._document is None:
            raise PdfServiceError("No hay ningún PDF abierto.")
        if not 0 <= page_index < len(self._document):
            raise PdfServiceError(f"Página fuera de rango: {page_index + 1}")

        cached = self._cache.get(page_index)
        if cached is not None:
            self._cache.move_to_end(page_index)
            return cached

        try:
            page = self._document.load_page(page_index)
            pixmap = page.get_pixmap(
                matrix=fitz.Matrix(self._render_scale, self._render_scale),
                colorspace=fitz.csRGB,
                alpha=False,
            )
            image = PageImage(
                width=pixmap.width,
                height=pixmap.height,
                pixels=bytes(pixmap.samples),
            )
        except Exception as exc:
            raise PdfServiceError(
                f"No se pudo renderizar la página {page_index + 1}."
            ) from exc

        self._cache[page_index] = image
        self._cache.move_to_end(page_index)

        while len(self._cache) > self._cache_size:
            self._cache.popitem(last=False)

        return image

    def render_spread(self, first_page: int) -> list[PageImage]:
        if not 0 <= first_page < self.page_count:
            return []
        pages = [self.render_page(first_page)]
        second_page = first_page + 1
        if second_page < self.page_count:
            pages.append(self.render_page(second_page))
        return pages

    def close(self) -> None:
        if self._document is not None:
            self._document.close()
        self._document = None
        self._path = None
        self._cache.clear()

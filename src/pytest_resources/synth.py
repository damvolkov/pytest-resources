"""pytest_resources.synth: on-the-fly objects and files behind optional extras.

The single vendor seam of the package: polyfactory synthesizes instances,
faker-file synthesizes files. :class:`pytest_resources.nodes.Resources` imports
this module lazily on first use, so the wheel behaves identically with or without
the backends — availability is probed, never assumed, and every public method
raises :class:`pytest_resources.errors.ExtraNotInstalledError` naming the exact
extra to install when its backend is absent.
"""

from __future__ import annotations

import contextlib
import importlib
import random
from dataclasses import dataclass
from importlib.util import find_spec
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Final, TypedDict, cast

from pytest_resources.errors import ExtraNotInstalledError, ResourceError
from pytest_resources.formats import _SUFFIXES, FileType

if TYPE_CHECKING:
    from collections.abc import Mapping

##### PRIVATE #####

_PIL_IMAGE: Final = "faker_file.providers.image.pil_generator.PilImageGenerator"
_PIL_PDF: Final = "faker_file.providers.pdf_file.generators.pil_generator.PilPdfGenerator"


@dataclass(frozen=True, slots=True)
class _Recipe:
    """Where one synthetic format lives inside faker-file."""

    provider: str
    klass: str
    method: str
    generator_kwarg: str | None = None
    generator: str | None = None


def _recipe(provider: str, klass: str, method: str, gen_kwarg: str | None = None, gen: str | None = None) -> _Recipe:
    return _Recipe(f"faker_file.providers.{provider}", klass, method, gen_kwarg, gen)


_FILES: Final[Mapping[FileType, _Recipe]] = MappingProxyType(
    {
        FileType.BINARY: _recipe("bin_file", "BinFileProvider", "bin_file"),
        FileType.TEXT: _recipe("txt_file", "TxtFileProvider", "txt_file"),
        FileType.CSV: _recipe("csv_file", "CsvFileProvider", "csv_file"),
        FileType.JSON: _recipe("json_file", "JsonFileProvider", "json_file"),
        FileType.XML: _recipe("xml_file", "XmlFileProvider", "xml_file"),
        FileType.PDF: _recipe("pdf_file", "PdfFileProvider", "pdf_file", "pdf_generator_cls", _PIL_PDF),
        FileType.DOCX: _recipe("docx_file", "DocxFileProvider", "docx_file"),
        FileType.XLSX: _recipe("xlsx_file", "XlsxFileProvider", "xlsx_file"),
        FileType.PPTX: _recipe("pptx_file", "PptxFileProvider", "pptx_file"),
        FileType.EPUB: _recipe("epub_file", "EpubFileProvider", "epub_file"),
        FileType.RTF: _recipe("rtf_file", "RtfFileProvider", "rtf_file"),
        FileType.ODT: _recipe("odt_file", "OdtFileProvider", "odt_file"),
        FileType.ODS: _recipe("ods_file", "OdsFileProvider", "ods_file"),
        FileType.ODP: _recipe("odp_file", "OdpFileProvider", "odp_file"),
        FileType.EML: _recipe("eml_file", "EmlFileProvider", "eml_file"),
        FileType.MP3: _recipe("mp3_file", "Mp3FileProvider", "mp3_file"),
        FileType.ZIP: _recipe("zip_file", "ZipFileProvider", "zip_file"),
        FileType.TAR: _recipe("tar_file", "TarFileProvider", "tar_file"),
        FileType.ICO: _recipe("ico_file", "IcoFileProvider", "ico_file", "image_generator_cls", _PIL_IMAGE),
        FileType.BMP: _recipe("bmp_file", "BmpFileProvider", "bmp_file", "image_generator_cls", _PIL_IMAGE),
        FileType.GIF: _recipe("gif_file", "GifFileProvider", "gif_file", "image_generator_cls", _PIL_IMAGE),
        FileType.JPEG: _recipe("jpeg_file", "JpegFileProvider", "jpeg_file", "image_generator_cls", _PIL_IMAGE),
        FileType.PNG: _recipe("png_file", "PngFileProvider", "png_file", "image_generator_cls", _PIL_IMAGE),
        FileType.TIFF: _recipe("tiff_file", "TiffFileProvider", "tiff_file", "image_generator_cls", _PIL_IMAGE),
        FileType.WEBP: _recipe("webp_file", "WebpFileProvider", "webp_file", "image_generator_cls", _PIL_IMAGE),
    }
)

### Bare names accepted by ``file``: every kind value plus every known suffix without its dot.
_ALIASES: Final[Mapping[str, FileType]] = MappingProxyType(
    {
        **{kind.value: kind for kind in FileType},
        **{suffix.removeprefix(".").casefold(): kind for suffix, kind in _SUFFIXES.items()},
    }
)

_POLYFACTORY_OPTIONAL_BACKENDS: Final[tuple[str, ...]] = (
    "pydantic_factory",
    "msgspec_factory",
    "attrs_factory",
    "sqlalchemy_factory",
    "beanie_odm_factory",
    "odmantic_odm_factory",
)


############################################################


class SynthProvider:
    """Random objects and files; the only symbol of the package that touches a synthesis backend."""

    __slots__ = ("_faker", "_files_backend", "_objects_backend", "_registered")

    def __init__(self) -> None:
        ### find_spec is cached by importlib: probing both backends at construction is free.
        self._objects_backend = find_spec("polyfactory") is not None
        self._files_backend = find_spec("faker_file") is not None
        self._faker: Any = None
        self._registered = False

    ##### PRIVATE #####

    def _common_require(self, method: str, extra: str, module: str, *, present: bool) -> None:
        if present:
            return
        msg = (
            f"`Resources.{method}()` requires the '{extra}' extra.\n"
            f'Install it with:  uv add --group test "pytest-resources[{extra}]"\n'
            f"Underlying import failed: {module}"
        )
        raise ExtraNotInstalledError(msg)

    def _common_seed(self, seed: int | None) -> int:
        ### Without an explicit seed the run's global RNG rules, so draws stay reproducible per session.
        return random.getrandbits(64) if seed is None else seed

    def _make_register(self) -> None:
        ### Optional model backends register their factories on import; absent ones are skipped, one by one.
        from polyfactory.exceptions import MissingDependencyException  # noqa: PLC0415 -- vendor seam

        for backend in _POLYFACTORY_OPTIONAL_BACKENDS:
            with contextlib.suppress(ImportError, MissingDependencyException):
                importlib.import_module(f"polyfactory.factories.{backend}")
        self._registered = True

    def _make_factory(self, spec: Any) -> tuple[Any, bool]:
        """Factory for a model or a bare hint; the bool flags a hint wrapped in a ``Holder``."""
        from polyfactory import BaseFactory  # noqa: PLC0415 -- vendor seam
        from polyfactory.exceptions import ParameterException  # noqa: PLC0415 -- vendor seam

        if not self._registered:
            self._make_register()
        try:
            return BaseFactory._get_or_create_factory(spec), False
        except ParameterException:
            ### A hint is not a model: it rides a runtime-built TypedDict and is unwrapped after.
            holder = TypedDict("holder", {"v": spec})  # noqa: UP013 -- the annotation exists only at runtime
            return BaseFactory._get_or_create_factory(holder), True

    @staticmethod
    def _file_recipe(kind: FileType | str) -> _Recipe:
        resolved = SynthProvider._file_of(kind)
        recipe = _FILES.get(resolved)
        if recipe is None:
            msg = f"pytest-resources cannot synthesize a {resolved.value!r} file — kinds with a recipe: {sorted(k.value for k in _FILES)}"
            raise ResourceError(msg)
        return recipe

    @staticmethod
    def _file_of(kind: FileType | str) -> FileType:
        """A kind, a bare name, a bare suffix or any filename with a recognised suffix resolves to a FileType."""
        match kind:
            case FileType() as known:
                return known
            case str() as text:
                stem = text.removeprefix(".").casefold()
                resolved = _ALIASES.get(Path(text).suffix.removeprefix(".").casefold()) or _ALIASES.get(stem)
                match resolved:
                    case FileType() as found:
                        return found
                    case _:
                        msg = f"not a synthesizable file kind: {kind!r}"
                        raise ResourceError(msg)
            case _:
                msg = f"not a synthesizable file kind: {kind!r}"
                raise ResourceError(msg)

    def _file_faker(self, seed: int) -> Any:
        if self._faker is None:
            from faker import Faker  # noqa: PLC0415 -- vendor seam

            self._faker = Faker()
        self._faker.seed_instance(seed)
        return self._faker

    @staticmethod
    def _file_create(recipe: _Recipe, name: str | None, faker: Any) -> Path:
        module = importlib.import_module(recipe.provider)
        provider = getattr(module, recipe.klass)(faker)
        kwargs: dict[str, Any] = {}
        if recipe.generator is not None and recipe.generator_kwarg is not None:
            kwargs[recipe.generator_kwarg] = recipe.generator
        if name is not None:
            kwargs["basename"] = Path(name).stem
        generated = getattr(provider, recipe.method)(**kwargs)
        return Path(cast("str", generated.data["filename"]))

    ############################################################

    ##### PUBLIC #####

    def make(self, spec: Any, /, *, seed: int | None = None, **fields: Any) -> Any:
        """One synthesized instance of a model class or type hint."""
        self._common_require("make", "objects", "polyfactory", present=self._objects_backend)
        factory, wrapped = self._make_factory(spec)
        factory.seed_random(self._common_seed(seed))
        built = factory.build(**fields)
        return built["v"] if wrapped else built

    def batch(self, spec: Any, /, n: int = 10, *, seed: int | None = None, **fields: Any) -> list[Any]:
        """``n`` synthesized instances of a model class or type hint."""
        self._common_require("batch", "objects", "polyfactory", present=self._objects_backend)
        factory, wrapped = self._make_factory(spec)
        factory.seed_random(self._common_seed(seed))
        built = factory.batch(n, **fields)
        return [item["v"] for item in built] if wrapped else built

    def file(self, kind: FileType | str, /, *, name: str | None = None, seed: int | None = None) -> Path:
        """A real synthetic file on disk; the returned path exists and is not empty."""
        self._common_require("file", "files", "faker-file", present=self._files_backend)
        recipe = self._file_recipe(kind)
        return self._file_create(recipe, name, self._file_faker(self._common_seed(seed)))

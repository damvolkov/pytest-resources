"""tests/unit: end-to-end proof that the pytest_resource_loaders hook and --resources-root work."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pytest


def test_loader_hook_and_cli_root(pytester: pytest.Pytester) -> None:
    res = Path(pytester.path) / "res"
    (res / "rows").mkdir(parents=True)
    (res / "rows" / "people.csv").write_text("name,age\nada,36\ngrace,45\n")

    pytester.makeconftest(
        """
        import csv, io
        from pytest_resources import FileType

        def pytest_resource_loaders(register):
            register({FileType.CSV: lambda b: list(csv.DictReader(io.StringIO(b.decode())))})
        """
    )
    pytester.makepyfile(
        test_hook="""
        def test_csv_parsed_by_hook(resources):
            people = resources.rows.people
            assert [p["name"] for p in people] == ["ada", "grace"]
        """
    )
    result = pytester.runpytest_subprocess(f"--resources-root={res}", "-p", "no:randomly")
    result.assert_outcomes(passed=1)


def test_multiple_roots_merged_by_hook(pytester: pytest.Pytester) -> None:
    base = Path(pytester.path) / "base"
    (base / "data").mkdir(parents=True)
    (base / "data" / "a.json").write_text('{"from": "base"}')
    (base / "primary.json").write_text('{"v": 1}')
    extra = Path(pytester.path) / "extra"
    (extra / "data").mkdir(parents=True)
    (extra / "data" / "a.json").write_text('{"from": "extra"}')
    (extra / "shared.json").write_text('{"v": 2}')

    pytester.makeconftest(
        f"""
        from pathlib import Path

        def pytest_resources_roots(roots):
            roots.append(Path({str(extra)!r}))
        """
    )
    pytester.makepyfile(
        test_multi="""
        def test_flat_merge_later_wins(resources):
            assert resources.primary["v"] == 1          # from the CLI base root
            assert resources.shared["v"] == 2           # from the hook-appended root
            assert resources.data.a["from"] == "extra"  # key clash: the later root wins
        """
    )
    result = pytester.runpytest_subprocess(f"--resources-root={base}", "-p", "no:randomly")
    result.assert_outcomes(passed=1)


def test_missing_default_root_is_created(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        test_empty="""
        def test_empty_tree_but_created(resources):
            assert resources.path.name == "resources"
            assert resources.keys() == []
        """
    )
    result = pytester.runpytest_subprocess("-p", "no:randomly")
    result.assert_outcomes(passed=1)
    assert (Path(pytester.path) / "tests" / "resources").is_dir()

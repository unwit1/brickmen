from __future__ import annotations

import csv
import importlib.util
from pathlib import Path


TOOL = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "knowledge"
    / "ingest_rebrickable_minifig_corpus.py"
)


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "ingest_rebrickable_minifig_corpus",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_csv(path: Path, rows: list[list[str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(rows)


def test_build_minimal_corpus(tmp_path: Path) -> None:
    tool = load_tool()
    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()

    datasets = {
        "minifigs": [
            ["fig_num", "name", "num_parts", "img_url"],
            ["fig-0001", "Test Hero", "3", "https://example.test/fig.png"],
        ],
        "inventories": [
            ["id", "version", "set_num"],
            ["1", "1", "set-1"],
            ["2", "1", "fig-0001"],
        ],
        "inventory_minifigs": [
            ["inventory_id", "fig_num", "quantity"],
            ["1", "fig-0001", "1"],
        ],
        "inventory_parts": [
            [
                "inventory_id",
                "part_num",
                "color_id",
                "quantity",
                "is_spare",
                "img_url",
            ],
            ["2", "head1", "1", "1", "f", ""],
            ["2", "torso1", "2", "1", "f", ""],
            ["2", "leg1", "3", "1", "f", ""],
        ],
        "parts": [
            ["part_num", "name", "part_cat_id", "part_material"],
            ["head1", "Head", "27", "Plastic"],
            ["torso1", "Torso", "27", "Plastic"],
            ["leg1", "Legs", "27", "Plastic"],
        ],
        "part_relationships": [
            ["rel_type", "child_part_num", "parent_part_num"],
        ],
        "elements": [
            ["element_id", "part_num", "color_id", "design_id"],
            ["e1", "head1", "1", "d1"],
        ],
        "colors": [
            ["id", "name", "rgb", "is_trans"],
            ["1", "Yellow", "FFFF00", "f"],
            ["2", "Blue", "0000FF", "f"],
            ["3", "Black", "000000", "f"],
        ],
        "sets": [
            [
                "set_num",
                "name",
                "year",
                "theme_id",
                "num_parts",
                "img_url",
            ],
            ["set-1", "Test Set", "2026", "10", "100", ""],
        ],
        "themes": [
            ["id", "name", "parent_id"],
            ["10", "Test Theme", ""],
        ],
    }

    for name, rows in datasets.items():
        write_csv(source / f"{name}.csv", rows)

    result = tool.build(source, output)

    assert result["minifig_rows"] == 1
    assert result["census_rows"] == 1
    assert (output / "official-minifigure-corpus.sqlite3").exists()

    line = (
        output / "official-minifigure-census.jsonl"
    ).read_text(encoding="utf-8")
    assert '"fig_num":"fig-0001"' in line
    assert '"name":"Test Hero"' in line
    assert '"part_num":"head1"' in line
    assert '"theme_id":"10"' in line


def test_missing_required_column_is_rejected(tmp_path: Path) -> None:
    tool = load_tool()
    path = tmp_path / "minifigs.csv"
    write_csv(path, [["fig_num", "name"], ["fig-1", "Broken"]])
    columns = tool.inspect_header(path)

    try:
        tool.validate_headers("minifigs", columns)
    except ValueError as exc:
        assert "num_parts" in str(exc)
    else:
        raise AssertionError("expected validation error")

from __future__ import annotations

from pathlib import Path


def test_column_mapping_is_applied_only_to_visual_width_provider() -> None:
    qml_path = Path(__file__).resolve().parents[1] / "qml" / "CalendarPage.qml"
    source = qml_path.read_text(encoding="utf-8")

    # Qt's columnWidthProvider receives a visual position, so this is the
    # one place where the persisted visual->logical map must be applied.
    assert "root.logicalColumn(column)" in source

    # Header/table delegates expose the logical QModelIndex column already.
    # Applying the visual mapping a second time would break sorting, flags
    # and semantic formatting after a drag.
    assert "root.tableModel.sortColumnIndex === column" in source
    assert "bridge.sortColumn(root.sourceKey, column)" in source
    assert "property int logicalColumnIndex: column" in source

    # Guard against reintroducing the previous double-mapping regression.
    assert source.count("root.logicalColumn(column)") == 1

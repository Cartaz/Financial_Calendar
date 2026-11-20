"""Column sorting of the canonical calendar view."""

from core.calendar_view import sort_rows


def _rows(values):
    return [{"actual": value, "event_name": str(i)} for i, value in enumerate(values)]


def test_economic_values_sort_by_signed_magnitude() -> None:
    rows = _rows(
        ["0.3%", "0.25%", "", "-0.5%", "-1.2%", "1.0%", "10K", "9.5K", "-0.1%"]
    )
    ascending = [row["actual"] for row in sort_rows(rows, "actual", False)]
    assert ascending == [
        "-1.2%",
        "-0.5%",
        "-0.1%",
        "0.25%",
        "0.3%",
        "1.0%",
        "9.5K",
        "10K",
        "",
    ]
    descending = [row["actual"] for row in sort_rows(rows, "actual", True)]
    assert descending[:3] == ["10K", "9.5K", "1.0%"]
    assert descending[-1] == "", "values without a number stay last"


def test_magnitude_suffixes_compare_across_units() -> None:
    rows = _rows(["1.2M", "950K", "1,250K"])
    assert [row["actual"] for row in sort_rows(rows, "actual", False)] == [
        "950K",
        "1.2M",
        "1,250K",
    ]


def test_text_columns_keep_natural_order() -> None:
    rows = [{"event_name": f"Event {i}"} for i in (10, 2, 1)]
    assert [row["event_name"] for row in sort_rows(rows, "event_name", False)] == [
        "Event 1",
        "Event 2",
        "Event 10",
    ]

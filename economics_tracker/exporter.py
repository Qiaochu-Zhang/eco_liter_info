from __future__ import annotations

from pathlib import Path

from economics_tracker.config import EXPORT_COLUMNS
from economics_tracker.models import Article

try:
    from openpyxl import Workbook
except ImportError as exc:  # pragma: no cover
    Workbook = None
    OPENPYXL_IMPORT_ERROR = exc
else:
    OPENPYXL_IMPORT_ERROR = None


def export_articles_to_excel(articles: list[Article], output_path: str | Path) -> Path:
    if Workbook is None:  # pragma: no cover
        raise RuntimeError(
            "openpyxl is required for Excel export"
        ) from OPENPYXL_IMPORT_ERROR

    workbook = Workbook()
    selected_sheet = workbook.active
    selected_sheet.title = "selected"
    rejected_sheet = workbook.create_sheet("rejected")

    _write_header(selected_sheet)
    _write_header(rejected_sheet)

    for article in articles:
        row = [article.to_row()[column] for column in EXPORT_COLUMNS]
        if article.decision == "selected":
            selected_sheet.append(row)
        else:
            rejected_sheet.append(row)

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(path)
    return path


def _write_header(sheet) -> None:
    sheet.append(list(EXPORT_COLUMNS))

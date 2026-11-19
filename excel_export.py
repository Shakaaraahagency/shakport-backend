"""Builds the Excel file that admins download."""
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

COLUMNS = [
    ("Reference", 14),
    ("Received (Lagos time)", 22),
    ("Name", 24),
    ("WhatsApp", 20),
    ("Email", 32),
    ("Service", 34),
    ("Message", 70),
    ("Sent from", 18),
]
DATE_COLUMN = 2
MESSAGE_COLUMN = 7


def build_workbook(rows):
    """Each row is a list in the same order as COLUMNS."""
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Quote requests"

    sheet.append([title for title, _ in COLUMNS])
    for number, (_, width) in enumerate(COLUMNS, start=1):
        header = sheet.cell(row=1, column=number)
        header.fill = PatternFill(start_color="8200C3", end_color="8200C3", fill_type="solid")
        header.font = Font(bold=True, color="FFFFFF")
        sheet.column_dimensions[header.column_letter].width = width

    for row in rows:
        sheet.append(row)
        for number in range(1, len(COLUMNS) + 1):
            cell = sheet.cell(row=sheet.max_row, column=number)
            cell.alignment = Alignment(vertical="top", wrap_text=number == MESSAGE_COLUMN)
            if number == DATE_COLUMN:
                cell.number_format = "dd mmm yyyy hh:mm"
            else:
                # A visitor could type =HYPERLINK(...) as their name. Stored as text, Excel never runs it.
                cell.value = str(cell.value)
                cell.data_type = "s"

    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions

    file_in_memory = BytesIO()
    workbook.save(file_in_memory)
    file_in_memory.seek(0)
    return file_in_memory

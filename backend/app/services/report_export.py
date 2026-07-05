"""TCO report exports (F-602): .xlsx with real numeric cells, and PDF."""
from io import BytesIO

from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.schemas.report import TCOReport

_HEADERS = [
    "Plate", "Make", "Model", "Fuel cost", "Service cost", "Document cost",
    "Total cost", "Km driven", "Cost / km", "Utilization %",
]


def _row_values(r) -> list:
    return [
        r.plate, r.make, r.model, r.fuel_cost, r.service_cost, r.document_cost,
        r.total_cost, r.km_driven, r.cost_per_km, r.utilization_pct,
    ]


def _totals_values(report: TCOReport) -> list:
    f = report.fleet
    return [
        "FLEET TOTAL", "", "", f.fuel_cost, f.service_cost, f.document_cost,
        f.total_cost, f.km_driven, f.cost_per_km, f.utilization_pct,
    ]


def tco_to_xlsx(report: TCOReport) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "TCO"
    ws.append([f"TCO report {report.date_from} – {report.date_to}"])
    ws.append(_HEADERS)
    # Values are appended as numbers, not strings, so Excel formulas work (DoD #4).
    for r in report.rows:
        ws.append(_row_values(r))
    ws.append(_totals_values(report))

    for col in ws.columns:
        width = max(len(str(c.value)) for c in col if c.value is not None)
        ws.column_dimensions[col[0].column_letter].width = min(width + 2, 40)

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def tco_to_pdf(report: TCOReport) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(A4),
        leftMargin=15 * mm, rightMargin=15 * mm, topMargin=15 * mm, bottomMargin=15 * mm,
    )
    styles = getSampleStyleSheet()
    title = Paragraph(
        f"FleetFlow — TCO report {report.date_from} – {report.date_to}", styles["Title"]
    )

    data = [_HEADERS]
    data += [
        [v if v is not None else "—" for v in _row_values(r)] for r in report.rows
    ]
    data.append([v if v is not None else "—" for v in _totals_values(report)])

    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e5e7eb")),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f9fafb")]),
            ]
        )
    )
    doc.build([title, Spacer(0, 6 * mm), table])
    return buf.getvalue()

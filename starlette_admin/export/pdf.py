"""PDF exporter: produces a ``.pdf`` table via *reportlab*."""

from __future__ import annotations

import io
from typing import TYPE_CHECKING, Any

from starlette_admin.export.base import BaseExporter

if TYPE_CHECKING:
    from starlette_admin.fields import BaseField


class PdfExporter(BaseExporter):
    content_type = "application/pdf"
    extension = "pdf"
    requires = "reportlab"

    async def generate(
        self,
        fields: list[BaseField],
        rows: list[dict[str, Any]],
    ) -> bytes:
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
            from reportlab.platypus import (
                Paragraph,
                SimpleDocTemplate,
                Table,
                TableStyle,
            )
        except ImportError as exc:
            raise ImportError(
                "The 'reportlab' package is required for PDF export. "
                "Install it with: pip install starlette-admin[pdf]"
            ) from exc

        buf = io.BytesIO()
        page_width, _ = landscape(A4)
        margin = 40
        n_cols = len(fields)
        col_width = (page_width - 2 * margin) / n_cols if n_cols else page_width

        if not n_cols:
            doc = SimpleDocTemplate(buf, pagesize=landscape(A4))
            doc.build([])
            return buf.getvalue()

        styles = getSampleStyleSheet()
        header_style = ParagraphStyle(
            "HeaderCell",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            textColor=colors.white,
            wordWrap="CJK",
        )
        cell_style = ParagraphStyle(
            "BodyCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            wordWrap="CJK",
        )

        def _cell(text: str, style: ParagraphStyle) -> Paragraph:
            return Paragraph(str(text).replace("\n", "<br/>"), style)

        data: list[list[Paragraph]] = [
            [_cell(f.label or f.name, header_style) for f in fields],
            *[
                [_cell(str(row.get(f.name, "") or ""), cell_style) for f in fields]
                for row in rows
            ],
        ]

        table = Table(data, colWidths=[col_width] * n_cols, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4A5568")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E0")),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#F7FAFC")],
                    ),
                ]
            )
        )

        doc = SimpleDocTemplate(
            buf,
            pagesize=landscape(A4),
            leftMargin=margin,
            rightMargin=margin,
            topMargin=margin,
            bottomMargin=margin,
        )
        doc.build([table])
        return buf.getvalue()

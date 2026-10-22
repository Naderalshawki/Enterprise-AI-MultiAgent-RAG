from pathlib import Path
from typing import Any, List, Optional

try:
    import pandas as pd
except ImportError:
    pd = None

from src.modules.rag.domain.entities import Document
from src.modules.rag.domain.exceptions import DocumentParsingException
from src.modules.rag.domain.value_objects import DocumentType
from src.modules.rag.infrastructure.loaders.base_loader import BaseDocumentLoader


class ExcelLoader(BaseDocumentLoader):
    """Extracts structured rows and sheets from CSV and Excel spreadsheets."""

    supported_extensions = {"xlsx", "xls", "csv"}

    def load(
        self,
        file_path: str,
        tenant_id: Optional[str] = None,
        max_rows_per_sheet: int = 1000,
        **kwargs: Any,
    ) -> Document:
        path = self.validate_file(file_path)

        if pd is None:
            raise DocumentParsingException(
                "حزمة pandas غير مثبتة. يرجى تثبيتها عبر: pip install pandas openpyxl"
            )

        ext = path.suffix.lower().lstrip(".")
        content_parts: List[str] = []
        sheets_metadata = []

        try:
            if ext == "csv":
                # Try UTF-8 then fallback to Windows Arabic / Latin encodings
                for encoding in ["utf-8-sig", "utf-8", "cp1256", "latin1"]:
                    try:
                        df = pd.read_csv(str(path), encoding=encoding)
                        break
                    except (UnicodeDecodeError, UnicodeError):
                        continue
                else:
                    df = pd.read_csv(str(path), encoding="utf-8", errors="ignore")

                sheet_name = "CSV_Data"
                text = self._dataframe_to_text(df, sheet_name, max_rows_per_sheet)
                content_parts.append(text)
                sheets_metadata.append({"sheet_name": sheet_name, "rows": len(df), "columns": list(df.columns)})
                doc_type = DocumentType.CSV

            else:
                # Excel file (.xlsx, .xls)
                excel_file = pd.ExcelFile(str(path))
                for sheet_name in excel_file.sheet_names:
                    df = pd.read_excel(excel_file, sheet_name=sheet_name)
                    text = self._dataframe_to_text(df, sheet_name, max_rows_per_sheet)
                    content_parts.append(text)
                    sheets_metadata.append({"sheet_name": sheet_name, "rows": len(df), "columns": list(df.columns)})
                doc_type = DocumentType.EXCEL

            metadata = {
                "sheets": sheets_metadata,
                "total_sheets": len(sheets_metadata),
            }

            full_content = "\n\n".join(content_parts)

            return self.create_document(
                path=path,
                content=full_content,
                doc_type=doc_type,
                metadata=metadata,
                tenant_id=tenant_id,
            )
        except Exception as err:
            raise DocumentParsingException(f"فشل في قراءة ملف البيانات المجدولة ({ext}): {err}") from err

    def _dataframe_to_text(self, df: Any, sheet_name: str, max_rows: int) -> str:
        """Converts tabular rows into natural contextual sentences for vector indexing."""
        lines = [f"=== ورقة العمل: {sheet_name} (الأعمدة: {', '.join(map(str, df.columns))}) ==="]

        # Limit rows if excessively huge to avoid blowing up memory
        sample_df = df.head(max_rows)
        for idx, row in sample_df.iterrows():
            row_elements = [
                f"{col}: {val}" for col, val in row.items() if pd.notna(val)
            ]
            if row_elements:
                lines.append(f"سجل {idx + 1}: " + " | ".join(row_elements))

        if len(df) > max_rows:
            lines.append(f"... (تم اقتطاع {len(df) - max_rows} سجل إضافي)")

        return "\n".join(lines)

import logging
import os
import re
import pandas as pd
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine

logger = logging.getLogger(__name__)


class CSVIngestionService:
    def __init__(self, database_url: str):
        self.engine: AsyncEngine = create_async_engine(database_url)

    def _sanitize_table_name(self, filename: str) -> str:
        base_name = os.path.splitext(filename)[0]
        safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', base_name).lower()
        if not safe_name[0].isalpha():
            safe_name = "tbl_" + safe_name
        return safe_name

    async def ingest_csv(self, file_path: str, original_filename: str) -> str:
        try:
            table_name = self._sanitize_table_name(original_filename)
            
            if original_filename.endswith(".xlsx"):
                df = pd.read_excel(file_path)
            else:
                df = pd.read_csv(file_path)
            
            # 1. تنظيف أسماء الأعمدة
            df.columns = [re.sub(r'[^a-zA-Z0-9_]', '_', str(c)).lower() for c in df.columns]

            # 2. تحويل الأرقام العربية لإنجليزية
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str).str.replace('٥', '5', regex=False).str.replace('٠', '0', regex=False).str.replace('٫', '.', regex=False).str.replace('٬', '', regex=False)

            # 🔥 3. السر هنا: إجبار تحويل الأعمدة اللي فيها أرقام لـ Float
            for col in df.columns:
                # نستبدل أي حروف غريبة (زي ??? أو not-json) بـ None (فراغ)
                df[col] = df[col].replace(r'[^\d\.\-]', None, regex=True)
                # نحول العمود لرقم، ولو فيه حاجة مش رقم بنخليها None
                df[col] = pd.to_numeric(df[col], errors='coerce')

            # 4. رفع البيانات
            async with self.engine.begin() as conn:
                await conn.run_sync(
                    lambda sync_conn: df.to_sql(
                        name=table_name,
                        con=sync_conn,
                        if_exists='replace', # بيمسح القديم وينشئ جديد
                        index=False
                    )
                )

            logger.info(f"[CSVIngestion] Successfully created table '{table_name}' with {len(df)} rows.")
            return table_name
            
        except Exception as e:
            logger.error(f"[CSVIngestion] Failed to ingest CSV: {str(e)}")
            raise e
import zipfile
from pathlib import Path
import panel as pn
import psycopg2
from io import BytesIO, StringIO
import pandas as pd
from config.dev import _HOST, _PORT, _DB, _UID, _PWD
from shared.tdm_logging import logger, log_error, class_method_name
from shared.sql import PGSQL
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side

pgsql = PGSQL()

class BOM_ManagementBackend:
    def __init__(self):
        # ===== CONFIG =====
        self.INPUT_DIR = Path("apps/TXT_to_CSV/input_file")
        self.OUTPUT_DIR = Path("apps/TXT_to_CSV/output_file")

        self.INPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # ===== WIDGETS =====
        self.input_select = pn.widgets.Select(
            name="📂 Input TXT Files",
            options=[],
            size=10
        )

        self.output_select = pn.widgets.Select(
            name="📂 Output CSV Files",
            options=[],
            size=10
        )

        self.upload_input = pn.widgets.FileInput(
            accept=".txt",
            multiple=True
        )

        self.btn_upload = pn.widgets.Button(
            name="⬆ Upload",
            button_type="primary"
        )

        self.btn_delete_input = pn.widgets.Button(
            name="🗑 Delete Input",
            button_type="danger"
        )

        self.btn_delete_output = pn.widgets.Button(
            name="🗑 Delete Output",
            button_type="danger"
        )

        self.btn_download_output = pn.widgets.FileDownload(
            label="⬇ Download Output",
            button_type="success",
            auto=True,
            disabled = True
        )

        self.btn_download_all = pn.widgets.FileDownload(
            label="⬇ Download All Output",
            button_type="success",
            button_style="outline",
            auto=True,
            disabled=True
        )

        self.btn_refresh = pn.widgets.Button(
            name="🔄 Refresh",
            button_type="primary"
        )

        # ===== BIND EVENTS =====
        self.btn_refresh.on_click(self.refresh_all)
        self.btn_upload.on_click(self.upload_files)
        self.btn_delete_input.on_click(self.delete_input)
        self.btn_delete_output.on_click(self.delete_output)
        self.output_select.param.watch(
            self.update_download_button,
            "value"
        )
        self.btn_download_all.callback = self.download_all_outputs

        # initial load
        self.refresh_all()

    # ===== UTILS FILE=====
    def get_files(self, folder, suffix=None):
        files = folder.glob(f"*{suffix}") if suffix else folder.iterdir()
        return sorted([f.name for f in files if f.is_file()])

    # ===== LOGIC FILE =====
    def refresh_all(self, event=None):
        self.input_select.options = []
        self.output_select.options = []

        self.input_select.options = self.get_files(self.INPUT_DIR, ".txt")
        self.output_select.options = self.get_files(self.OUTPUT_DIR, ".csv")

        self.btn_download_all.disabled = len(self.output_select.options) == 0

    def upload_files(self, event=None):
        if not self.upload_input.value:
            return

        for filename, content in zip(
            self.upload_input.filename,
            self.upload_input.value
        ):
            with open(self.INPUT_DIR / filename, "wb") as f:
                f.write(content)

        self.upload_input.value = None
        self.refresh_all()

    def delete_input(self, event=None):
        if self.input_select.value:
            path = self.INPUT_DIR / self.input_select.value
            if path.exists():
                path.unlink()
        self.refresh_all()

    def delete_output(self, event=None):
        if self.output_select.value:
            path = self.OUTPUT_DIR / self.output_select.value
            if path.exists():
                path.unlink()
        self.refresh_all()

    def update_download_button(self, event=None):
        if not self.output_select.value:
            self.btn_download_output.disabled = True
            return

        file_path = self.OUTPUT_DIR / self.output_select.value
        if file_path.exists():
            self.btn_download_output.file = file_path
            self.btn_download_output.filename = file_path.name
            self.btn_download_output.disabled = False

    def download_all_outputs(self):
        csv_files = list(self.OUTPUT_DIR.glob("*.csv"))
        if not csv_files:
            self.btn_download_all.disabled = True
            return

        zip_path = self.OUTPUT_DIR / "output_all.zip"

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in csv_files:
                zf.write(file, arcname=file.name)

        self.btn_download_all.file = zip_path
        self.btn_download_all.filename = "output_all.zip"
        self.btn_download_all.disabled = False

    def pg_connect(self):
        conn = psycopg2.connect(
            host=_HOST,
            port=_PORT,
            dbname=_DB,
            user=_UID,
            password=_PWD
        )
        conn.autocommit = False
        return conn
    
    def fetch_data(self) -> pd.DataFrame:
        logger.info(f"| Fetching data in BOM table")
        sql = """SELECT item_id, description FROM dbo.bom_master"""
        summary_df = pd.DataFrame()
        try:
            summary_df = pgsql.sql_to_df(query=sql, db='BOM_Management', mod='BOM_data')
            
            return summary_df
        except Exception as ex:
            logger.error(f"| Exception | {str(ex)}")
            return summary_df

    def insert_into_bom_master(self, item_id, description):
        logger.info(f"| Insert data into BOM table")
        conn = self.pg_connect()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO dbo.bom_master (item_id, description)
                VALUES (%s, %s)
                ON CONFLICT (item_id) DO NOTHING
                """,
                (item_id, description)
            )
            conn.commit()
            return f"items inserted successfully!"
        except Exception as e:
            conn.rollback()
            logger.error(f"| Error inserting data: {e}")
        finally:
            cursor.close()
            conn.close()

    def update_bom_master_only(self, item_id, description):
        logger.info(f"| Update data in BOM table")
        conn = self.pg_connect()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE dbo.bom_master
                SET description = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE item_id = %s;
                """,
                (description, item_id)
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"| Error updating item {item_id}: {e}")
        finally:
            cursor.close()
            conn.close()

    def delete_bom_master_only(self, item_id):
        logger.info(f"| Delete data {item_id} in BOM table")
        conn = self.pg_connect()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                DELETE FROM dbo.bom_master
                WHERE item_id = %s
                """,
                (item_id,)
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"| Error deleting item {item_id}: {e}")
        finally:
            cursor.close()
            conn.close()

    def csv_download_callback(self):
        try:
            df = self.fetch_data()

            if df is None or df.empty:
                logger.warning("CSV Download: No data available")
                return None

            logger.info(f"CSV Download triggered: {len(df)} rows")
            df_formatted = df.copy()
            csv_data = df_formatted.to_csv(index=False)
            return StringIO(csv_data)

        except Exception as e:
            log_error(e)
            return None
        
    def excel_download_callback(self):
        df = self.fetch_data()

        # Create a BytesIO object to save the Excel file in memory
        output = BytesIO()

            # Create a workbook and add a new worksheet
        wb = Workbook()
        wb.remove(wb.active)

        sheet_title = "BOM Report"
        ws = wb.create_sheet(title=sheet_title[:31])

        # Write the header row
        ws['A1'] = 'item_id'
        ws['B1'] = 'description'

        # Format headers to Excel sheet
        header_align = Alignment(horizontal='center', vertical='center')
        header_font = Font(size=11, bold=True, color='FFFFFFFF')
        header_fill = PatternFill(start_color='006EB8', end_color='006EB8', fill_type='solid')
        for col_idx in range(1, 3):
            for row_idx in range(1, 2):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.alignment = header_align
                cell.font = header_font
                cell.fill = header_fill

        # Write DataFrame data to Excel sheet
        for r_idx, row in enumerate(df.itertuples(index=False), start=2):
            for c_idx, value in enumerate(row, start=1):
                cell = ws.cell(row=r_idx, column=c_idx, value=value)
                if c_idx > 1:
                    cell.alignment = Alignment(horizontal='center')
                    if c_idx in [4, 7, 10, 13]:
                        cell.alignment = Alignment(horizontal='center')
                        ftt_font = Font(color='B71C1C')
                        ftt_index = float((cell.value).replace(' %', ''))
                        if ftt_index >= 97.5:
                            ftt_font = Font(color='2E7D32')
                        elif 92.5 <= ftt_index < 97.5:
                            ftt_font = Font(color='E65100')
                        cell.font = ftt_font
                else:
                    cell.alignment = Alignment(horizontal='left')
        # Save the workbook to the BytesIO object
        wb.save(output)
        output.seek(0)
        return output
    
        
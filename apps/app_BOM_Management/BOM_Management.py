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
    
        
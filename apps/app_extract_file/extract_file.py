from io import StringIO
import re
import os
import pandas as pd
import psycopg2
from config.dev import _HOST, _PORT, _DB, _UID, _PWD
from shared.tdm_logging import logger, log_error, class_method_name

class extract_file_backend:
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


    def extract_tubing_with_item_number(self, file_path,keyword):
        logger.info(f"| Extract data from txt file")
        # default keyword
        if not keyword or not keyword.strip():
            keyword = ""

        # Set var
        tubing_items = []
        current_item_number = None
        Inv_Unt = None
        Net_Quantity = None
        seen_items = set()
        norm_keyword = re.sub(r"\s+", " ", keyword).strip().lower()

        # read txt file
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # Get data form txt file
        for line in lines:
            if '|' in line:
                columns = [col.strip() for col in line.split('|')]
                if len(columns) > 2:
                    current_item_number = columns[2]
                    Inv_Unt = columns[11]
                    Net_Quantity = columns[12]
            match = re.search(r'"([^"]+)"', line)
            if match and current_item_number:
                desc = match.group(1).strip()
                norm_desc = re.sub(r"\s+", " ", desc).strip().lower()
                if norm_keyword in norm_desc and current_item_number not in seen_items:
                    tubing_items.append((current_item_number, desc, Inv_Unt, Net_Quantity))
                    seen_items.add(current_item_number)
        
        return tubing_items
    
    def insert_data_list_to_BOM_items(self, data_list):
        logger.info(f"| Insert data from txt file into BOM table")
        conn = self.pg_connect()
        cursor = conn.cursor()
        try:
            rows_inserted = 0
            skipped_items = []
            for item_id, description in data_list:
                cursor.execute(
                    """
                    INSERT INTO dbo.BOM_items (item_id, description)
                    VALUES (%s, %s)
                    ON CONFLICT (item_id) DO NOTHING
                    """,
                    (item_id, description)
                )
                if cursor.rowcount > 0:
                    rows_inserted += 1
                else:
                    skipped_items.append(item_id)
            conn.commit()
            msg = f"Inserted: {rows_inserted} items"
            if skipped_items:
                msg += f"\nSkipped (already existed): {len(skipped_items)} items"
                msg += "\nDuplicate item_id: " + ", ".join(skipped_items)
            return msg
        except Exception as e:
            conn.rollback()
            logger.error(f"| Error inserting data: {e}")
        finally:
            cursor.close()
            conn.close()


    def Matching_file_with_DB(self,data_from_txt):
        conn = self.pg_connect()
        cursor = conn.cursor()
        try:
            logger.info(f"| Matching txt file with DB")
            cursor.execute("SELECT item_id FROM dbo.BOM_items")
            db_items = {row[0] for row in cursor.fetchall()}
        except Exception as e:
            conn.rollback()
            logger.error(f"| Error inserting data: {e}")
            return []
        finally:
            cursor.close()
            conn.close()

        items_in_db = []
        for item in data_from_txt:
            if item[0] in db_items:
                items_in_db.append((item[0], item[1], item[2], item[3]))
        
        return items_in_db
    
    def csv_download_callback(self,data):
        try:
            if len(data) == 0 :
                logger.warning("| CSV Download: No data available plese extract txt first")
                return None
        
            logger.info(f"| CSV Download triggered: {len(data)} rows")
            df_formatted = data.copy()
            csv_data = df_formatted.to_csv(index=False)
            return StringIO(csv_data)

        except Exception as e:
            logger.warning("| Error from download in extract file : {e}")
            return None
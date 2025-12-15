import pandas as pd
from shared.tdm_logging import logger
from shared.sql import PGSQL
from sqlalchemy import create_engine, text
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import os
import re


pgsql = PGSQL()

WATCH_FOLDER = "apps/TXT_to_CSV/input_file"
OUTPUT_FOLDER = "apps/TXT_to_CSV/output_file"

class TxtFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return

        # read only .txt file
        if event.src_path.endswith(".txt"):
            self.process_file(event.src_path)

    def process_file(self, file_path):
        # Delay to allow the file to finish writing first.
        time.sleep(0.5)

        try:
            logger.info(f"| Convert txt to CSV")

            tubing_items = []
            current_item_number = None
            Inv_Unt = None
            Net_Quantity = None
            seen_items = set()

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
                if match and current_item_number and current_item_number not in seen_items:
                    desc = match.group(1).strip()
                    tubing_items.append((current_item_number, desc, Inv_Unt, Net_Quantity))
                    seen_items.add(current_item_number)

            Item_In_DB = Matching_file_with_DB(tubing_items)
            
            # Create DataFrame
            df =  pd.DataFrame(Item_In_DB, columns=["Item ID", "Description", "Inv Unt", "Net Quantity"])
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            df["chassi"] = base_name

            # SAVE CSV FILE
            os.makedirs(OUTPUT_FOLDER, exist_ok=True)
            output_path = os.path.join(OUTPUT_FOLDER, f"{base_name}.csv")
            df.to_csv(output_path, index=False, encoding="utf-8-sig")

        except Exception as e:
            logger.warning(f"| Cann't read file : {e}")

def Matching_file_with_DB(data_from_txt):
    query = "SELECT item_id FROM dbo.bom_master"

    engine = create_engine(pgsql.connect_url(db=""), echo=False)

    try:
        with engine.connect() as conn:
            result = conn.execute(text(query))
            db_items = {row[0] for row in result.fetchall()}

    except Exception as e:
        logger.error(f"| Error querying database: {e}")
        return []

    items_in_db = [
        (item[0], item[1], item[2], item[3])
        for item in data_from_txt
        if item[0] in db_items
    ]

    return items_in_db


def start_watchdog():
    observer = Observer()
    event_handler = TxtFileHandler()
    observer.schedule(event_handler, WATCH_FOLDER, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()

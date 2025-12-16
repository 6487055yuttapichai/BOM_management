import io
import panel as pn
import psycopg2
from io import BytesIO, StringIO
import pandas as pd
from config.dev import _HOST, _PORT, _DB, _UID, _PWD
from shared.downloads import excel_format
from shared.tdm_logging import logger, log_error, class_method_name
from shared.sql import PGSQL
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

pgsql = PGSQL()

class BOM_ManagementBackend:
    def __init__(self):
        # ===== UI WIDGETS =====
        self.insert_button = pn.widgets.Button(
            name="Add new item",
            button_type="primary"
        )

        self.update_button = pn.widgets.Button(
            name="Uupdate item",
            button_type="success"
        )

        self.delete_button = pn.widgets.Button(
            name="Delete item ",
            button_type="danger"
        )

        self.output_area = pn.pane.Markdown("", sizing_mode="stretch_width")

        self.search_box = pn.widgets.TextInput(
            name="Search",
            placeholder="Search Item ID or description..."
        )

        # ---- insert manual
        self.item_id = pn.widgets.TextInput(placeholder="Enter item id", width=250)
        self.description = pn.widgets.TextInput(placeholder="Enter description", width=250)
        self.type = pn.widgets.TextInput(placeholder="Enter type", width=250)
        self.nominal_tubing_size = pn.widgets.TextInput(placeholder="Enter nominal tubing size", width=250)
        self.color = pn.widgets.TextInput(placeholder="Enter color", width=250)
        self.tubing = pn.widgets.TextInput(placeholder="Enter tubing", width=250)
        self.tubing_tolerance = pn.widgets.TextInput(placeholder="Enter tubing tolerance", width=250)
        self.wall_thickness = pn.widgets.TextInput(placeholder="Enter wall thickness", width=250)
        self.wall_thickness_tolerance = pn.widgets.TextInput(placeholder="Enter wall thickness tolerance", width=250)

        self.insert_manual_button = pn.widgets.Button(
            name="Add new Row",
            button_type="primary"
        )
        
        
        self.btn_save_insert = pn.widgets.Button(name="Save", button_type="primary")
        self.btn_cancel_insert = pn.widgets.Button(name="Cancel")

        self.pop_up_insert_form = pn.layout.Modal(
            pn.Column(
                pn.pane.Markdown("### insert form"),
                pn.Row(pn.pane.Markdown("**Item_id :**", width=80), self.item_id),
                pn.Row(pn.pane.Markdown("**description :**", width=80), self.description),
                pn.Row(pn.pane.Markdown("**type :**", width=80), self.type),
                pn.Row(pn.pane.Markdown("**nominal_tubing_size :**", width=80), self.nominal_tubing_size),
                pn.Row(pn.pane.Markdown("**color :**", width=80), self.color),
                pn.Row(pn.pane.Markdown("**tubing :**", width=80), self.tubing),
                pn.Row(pn.pane.Markdown("**tubing_tolerance :**", width=80), self.tubing_tolerance),
                pn.Row(pn.pane.Markdown("**wall_thickness :**", width=80), self.wall_thickness),
                pn.Row(pn.pane.Markdown("**wall_thickness_tolerance :**", width=80), self.wall_thickness_tolerance),
                pn.Row(self.btn_save_insert, self.btn_cancel_insert)
            ),
            open=False,
            width=1000,
            height=1200
        )

        # ---- table
        self.table = pn.widgets.Tabulator(
            pagination="local",
            page_size=20,
            sizing_mode="stretch_width",
            show_index=False,
            selectable=True
        )

        # ---- downloads
        self.btn_table_csv_download = pn.widgets.FileDownload(
            self.csv_download_callback(),
            filename="BOM.csv",
            auto=True,
            embed=False,
            button_style="outline",
            button_type="success",
            height=32
        )

        self.btn_table_excel_download = pn.widgets.FileDownload(
            self.excel_download_callback(),
            filename="BOM.xlsx",
            embed=False,
            button_style="outline",
            button_type="success",
            height=32
        )

        

        # ===== BIND EVENTS =====
        self.insert_button.on_click(lambda e: setattr(self.pop_up_insert_form, "open", True))
        self.btn_cancel_insert.on_click(lambda e: setattr(self.pop_up_insert_form, "open", False))
        self.update_button.on_click(self.update_row)
        self.delete_button.on_click(self.delete_row)
        self.search_box.param.watch(self.filter_table, "value")


    # ===== LOGIC Manange Page=====
    def select_data(self):
        rows = self.fetch_data()
        if rows is not None and not rows.empty:
            self.table.value = rows
        else:
            self.table.value = pd.DataFrame(columns=["item_id", "description"])

    def update_row(self, event):
        if not self.table.selection:
            self.output_area.object = "### Please select row for update"
            return

        row = self.table.value.iloc[self.table.selection[0]]
        msg = self.update_bom_master(row["item_id"], row["description"])
        self.output_area.object = msg

    def delete_row(self, event):
        if not self.table.selection:
            self.output_area.object = "### Please select row for delete"
            return

        row = self.table.value.iloc[self.table.selection[0]]
        msg = self.delete_bom_master(row["item_id"])
        self.output_area.object = msg
        self.table.value = self.table.value.drop(self.table.selection[0]).reset_index(drop=True)

    def insert_manual_data(self, event):
        item = self.manual_item_id.value.strip()
        desc = self.manual_description.value.strip()

        if not item or not desc:
            self.output_area.object = "Please fill in both fields"
            return

        self.table.stream(pd.DataFrame([[item, desc]], columns=["item_id", "description"]))
        msg = self.insert_into_bom_master(item, desc)
        self.output_area.object = msg

        self.manual_item_id.value = ""
        self.manual_description.value = ""

    def filter_table(self, event):
        keyword = self.search_box.value.lower().strip()
        if not keyword:
            self.select_data()
            return

        df = self.table.value
        self.table.value = df[
            df["item_id"].str.lower().str.contains(keyword) |
            df["description"].str.lower().str.contains(keyword)
        ]

    # ===== LOGIC Manange DB=====
    def fetch_data(self) -> pd.DataFrame:
        logger.info(f"| Fetching data in BOM table")
        sql = """SELECT item_id, description, type, nominal_tubing_size, color, tubing, tubing_tolerance, wall_thickness, wall_thickness_tolerance FROM dbo.bom_master"""
        summary_df = pd.DataFrame()
        try:
            summary_df = pgsql.sql_to_df(query=sql, db='BOM_Management', mod='BOM_data')
            
            return summary_df
        except Exception as ex:
            logger.error(f"| Exception | {str(ex)}")
            return summary_df

    def insert_into_bom_master(self,
            item_id,
            description,
            type,
            nominal_tubing_size,
            color,
            tubing,
            tubing_tolerance,
            wall_thickness,
            wall_thickness_tolerance
        ):
        query = """
        INSERT INTO dbo.bom_master (item_id, description, type, nominal_tubing_size, color, tubing, tubing_tolerance, wall_thickness, wall_thickness_tolerance)
        VALUES
            (
                :item_id,
                :description,
                :type,
                :nominal_tubing_size,
                :color,
                :tubing,
                :tubing_tolerance,
                :wall_thickness,
                :wall_thickness_tolerance
            );
        """

        params = {
            "item_id": item_id,
            "description": description,
            "type": type,
            "nominal_tubing_size" : nominal_tubing_size,
            "color": color,
            "tubing": tubing,
            "tubing_tolerance": tubing_tolerance,
            "wall_thickness": wall_thickness,
            "wall_thickness_tolerance": wall_thickness_tolerance,
        }

        engine = create_engine(pgsql.connect_url(db=''), echo=False)

        try:
            with engine.begin() as conn:
                conn.execute(text(query), params)
        except SQLAlchemyError as e:
            logger.error(f"| Error updating item {item_id}: {e}")

    def update_bom_master(self,
            item_id,
            description,
            type,
            nominal_tubing_size,
            color,
            tubing,
            tubing_tolerance,
            wall_thickness,
            wall_thickness_tolerance
        ):
        query = """
            UPDATE dbo.bom_master
            SET
                description = :description,
                type = :type,
                nominal_tubing_size = :nominal_tubing_size,
                color = :color,
                tubing = :tubing,
                tubing_tolerance = :tubing_tolerance,
                wall_thickness = :wall_thickness,
                wall_thickness_tolerance = :wall_thickness_tolerance,
                updated_at = CURRENT_TIMESTAMP
            WHERE item_id = :item_id;
            """
        params = {
            "item_id": item_id,
            "description": description,
            "type": type,
            "nominal_tubing_size": nominal_tubing_size,
            "color": color,
            "tubing": tubing,
            "tubing_tolerance": tubing_tolerance,
            "wall_thickness": wall_thickness,
            "wall_thickness_tolerance": wall_thickness_tolerance,
        }

        engine = create_engine(pgsql.connect_url(db=''), echo=False)
        try:
            with engine.begin() as conn:
                conn.execute(text(query), params)
        except SQLAlchemyError as e:
            logger.error(f"| Error updating item {item_id}: {e}")

    def delete_bom_master(self, item_id):
        query = """
        DELETE FROM dbo.bom_master
        WHERE item_id = :item_id;
        """

        params = {
            "item_id": item_id
        }

        engine = create_engine(pgsql.connect_url(db=''), echo=False)

        try:
            with engine.begin() as conn:
                conn.execute(text(query), params)
        except SQLAlchemyError as e:
            logger.error(f"| Error deleting item {item_id}: {e}")

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
        workbook = excel_format(df, "BOM_Master")
        output = io.BytesIO()
        workbook.save(output)
        output.seek(0)

        return output
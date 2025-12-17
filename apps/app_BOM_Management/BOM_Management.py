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
        self.output_area = pn.pane.Markdown("", sizing_mode="stretch_width")

        self.insert_button = pn.widgets.Button(
            name="Add new item",
            button_type="primary"
        )

        self.delete_button = pn.widgets.Button(
            name="Delete item ",
            button_type="danger"
        )

        self.search_box = pn.widgets.TextInput(
            name="Search",
            placeholder="Search Item ID or description..."
        )

        # ---- insert manual
        self.item_id_insert = pn.widgets.TextInput(placeholder="Enter item id EX.(00000001)", width=250)
        self.description_insert = pn.widgets.TextInput(placeholder="Enter description EX.(TUBING)", width=250)
        self.type_insert = pn.widgets.TextInput(placeholder="Enter type EX.(A, B)", width=250)
        self.nominal_tubing_size_insert = pn.widgets.TextInput(placeholder="Enter nominal tubing size EX.(1/2)", width=250)
        self.color_insert = pn.widgets.TextInput(placeholder="Enter color EX.(GREEN)", width=250)
        self.tubing_insert = pn.widgets.FloatInput(placeholder="Enter tubing",value=5., step=1e-1, start=0, end=100 ,width=250)
        self.tubing_tolerance_insert = pn.widgets.FloatInput(placeholder="Enter tubing tolerance",value=5., step=1e-1, start=0, end=100 ,width=250)
        self.wall_thickness_insert = pn.widgets.FloatInput(placeholder="Enter wall thickness", value=5., step=1e-1, start=0, end=100 ,width=250)
        self.wall_thickness_tolerance_insert = pn.widgets.FloatInput(placeholder="Enter wall thickness tolerance",value=5., step=1e-1, start=0, end=100 ,width=250)

        self.insert_manual_button = pn.widgets.Button(
            name="Add new Row",
            button_type="primary"
        )
        
        
        self.btn_save_insert = pn.widgets.Button(name="Save", button_type="primary", width=250)
        self.btn_cancel_insert = pn.widgets.Button(name="Cancel", width=250)

        self.pop_up_insert_form = pn.layout.Modal(
            pn.Column(
                pn.pane.Markdown("### insert form"),
                pn.Row(pn.pane.Markdown("**Item id :**", width=110), self.item_id_insert),
                pn.Row(pn.pane.Markdown("**Description :**", width=110), self.description_insert),
                pn.Row(pn.pane.Markdown("**Type :**", width=110), self.type_insert),
                pn.Row(pn.pane.Markdown("**Nominal tubing size :**", width=110), self.nominal_tubing_size_insert),
                pn.Row(pn.pane.Markdown("**Color :**", width=110), self.color_insert),
                pn.Row(pn.pane.Markdown("**Tubing :**", width=110), self.tubing_insert),
                pn.Row(pn.pane.Markdown("**Tubing \ntolerance :**", width=110), self.tubing_tolerance_insert),
                pn.Row(pn.pane.Markdown("**Wall \nthickness :**", width=110), self.wall_thickness_insert),
                pn.Row(pn.pane.Markdown("**Wall \nthickness \ntolerance :**", width=110), self.wall_thickness_tolerance_insert),
                pn.Row(self.btn_save_insert, self.btn_cancel_insert)
            ),
            open=False,
            width=600,
            height=650
        )


        # ---- Edit
        self.selected_row = {"row": None}
        self.selected_ID = pn.pane.Markdown("", width=110, sizing_mode="stretch_width")
        self.description_update = pn.widgets.TextInput(placeholder="Enter description", width=250)
        self.type_update = pn.widgets.TextInput(placeholder="Enter type", width=250)
        self.nominal_tubing_size_update = pn.widgets.TextInput(placeholder="Enter nominal tubing size", width=250)
        self.color_update = pn.widgets.TextInput(placeholder="Enter color", width=250)
        self.tubing_update = pn.widgets.FloatInput(placeholder="Enter tubing",value=5., step=1e-1, start=0, end=100 ,width=250)
        self.tubing_tolerance_update = pn.widgets.FloatInput(placeholder="Enter tubing tolerance",value=5., step=1e-1, start=0, end=100 ,width=250)
        self.wall_thickness_update = pn.widgets.FloatInput(placeholder="Enter wall thickness",value=5., step=1e-1, start=0, end=100 ,width=250)
        self.wall_thickness_tolerance_update = pn.widgets.FloatInput(placeholder="Enter wall thickness tolerance",value=5., step=1e-1, start=0, end=100 ,width=250)

        self.btn_save_edit = pn.widgets.Button(name="Save", button_type="primary")
        self.btn_cancel_edit = pn.widgets.Button(name="Cancel")

        self.pop_up_edit_form = pn.layout.Modal(
            pn.Column(
                pn.pane.Markdown("### Edit Note"),
                self.selected_ID,
                pn.Row(pn.pane.Markdown("**Description :**", width=110), self.description_update),
                pn.Row(pn.pane.Markdown("**Type :**", width=110), self.type_update),
                pn.Row(pn.pane.Markdown("**Nominal tubing size :**", width=110), self.nominal_tubing_size_update),
                pn.Row(pn.pane.Markdown("**Color :**", width=110), self.color_update),
                pn.Row(pn.pane.Markdown("**Tubing :**", width=110), self.tubing_update),
                pn.Row(pn.pane.Markdown("**Tubing \ntolerance**", width=110), self.tubing_tolerance_update),
                pn.Row(pn.pane.Markdown("**Wall \nthickness :**", width=110), self.wall_thickness_update),
                pn.Row(pn.pane.Markdown("**Wall \nthickness \ntolerance :**", width=110), self.wall_thickness_tolerance_update),
                pn.Row(self.btn_save_edit, self.btn_cancel_edit)
            ),
            open=False,
            width=600,
            height=650
        )



        # ---- table
        self.table = pn.widgets.Tabulator(
            buttons={"edit": '<button class="btn btn-dark btn-sm">Edit</button>'},
            pagination="local",
            page_size=20,
            sizing_mode="stretch_width",
            show_index=False,
            disabled=True,
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
        self.btn_save_insert.on_click(lambda e: self.save_click("insert"))
        self.btn_cancel_insert.on_click(lambda e: setattr(self.pop_up_insert_form,  "open", False))
        
        self.table.on_click(self.on_table_edit_click)
        self.btn_save_edit.on_click(lambda e: self.save_click("update"))
        self.btn_cancel_edit.on_click(lambda e: setattr(self.pop_up_edit_form, "open", False))
        self.delete_button.on_click(self.delete_row)
        self.search_box.param.watch(self.filter_table, "value")


    # ===== LOGIC Manange Page=====
    def select_data(self):
        rows = self.fetch_data()
        if rows is not None and not rows.empty:
            self.table.value = rows
        else:
            self.table.value = pd.DataFrame()

    def save_click(self, type):
        if type == "update" and self.selected_row.get("row"):
            row = self.selected_row["row"]
            self.update_bom_master(
                item_id = row["Item ID"],
                description = self.description_update.value,
                type = self.type_update.value,
                nominal_tubing_size = self.nominal_tubing_size_update.value,
                color = self.color_update.value,
                tubing = self.tubing_update.value,
                tubing_tolerance = self.tubing_tolerance_update.value,
                wall_thickness = self.wall_thickness_update.value,
                wall_thickness_tolerance = self.wall_thickness_tolerance_update.value
            )
            self.pop_up_edit_form.open = False
            self.select_data()

        if type == "insert":
            self.insert_into_bom_master(
                item_id = self.item_id_insert.value,
                description = self.description_insert.value,
                type = self.type_insert.value,
                nominal_tubing_size = self.nominal_tubing_size_insert.value,
                color = self.color_insert.value,
                tubing = self.tubing_insert.value,
                tubing_tolerance = self.tubing_tolerance_insert.value,
                wall_thickness = self.wall_thickness_insert.value,
                wall_thickness_tolerance = self.wall_thickness_tolerance_insert.value
            )
            self.pop_up_insert_form.open = False
            self.select_data()

    def on_table_edit_click(self, event):
        if event.column != "edit":
            return

        df = pd.DataFrame(self.table.value)
        row = df.iloc[event.row].to_dict()
        self.selected_row["row"] = row

        self.selected_ID.object = (
            f"**selected Item ID :** **{row.get('Item ID')}**  \n")

        self.description_update.value = row.get("Description","") or ""
        self.type_update.value = row.get("Type","") or ""
        self.nominal_tubing_size_update.value = row.get("Nominal Tubing Size","") or ""
        self.color_update.value = row.get("Color","") or ""
        self.tubing_update.value = float(row.get("Tubing") or 0)
        self.tubing_tolerance_update.value = float(row.get("Tubing Tolerance") or 0)
        self.wall_thickness_update.value = float(row.get("Wall Thickness") or 0)
        self.wall_thickness_tolerance_update.value = float(row.get("Wall Thickness Tolerance") or 0)


        self.pop_up_edit_form.open = True

    def delete_row(self, event):
        if not self.table.selection:
            self.output_area.object = "### Please select row for delete"
            return

        row = self.table.value.iloc[self.table.selection[0]]
        msg = self.delete_bom_master(row["Item ID"])
        self.output_area.object = msg
        self.table.value = self.table.value.drop(self.table.selection[0]).reset_index(drop=True)

    def filter_table(self, event):
        keyword = self.search_box.value.lower().strip()
        if not keyword:
            self.select_data()
            return

        df = self.table.value
        self.table.value = df[
            df["Item ID"].str.lower().str.contains(keyword) |
            df["Description"].str.lower().str.contains(keyword)
        ]

    # ===== LOGIC Manange DB=====
    def fetch_data(self) -> pd.DataFrame:
        sql = """SELECT item_id, description, type, nominal_tubing_size, color, tubing, tubing_tolerance, wall_thickness, wall_thickness_tolerance FROM dbo.bom_master"""
        df = pd.DataFrame()
        try:
            df = pgsql.sql_to_df(query=sql, db='BOM_Management', mod='BOM_data')
            
            summary_df = self.format_colum_name(df)
            return summary_df
        except Exception as ex:
            logger.error(f"| Exception | {str(ex)}")

    def format_colum_name(self,df):
        summary_df = df.rename(columns={
            "item_id" : "Item ID", 
            "description" : "Description" , 
            "type" : "Type", 
            "nominal_tubing_size" : "Nominal Tubing Size", 
            "color" : "Color", 
            "tubing" : "Tubing", 
            "tubing_tolerance" : "Tubing Tolerance", 
            "wall_thickness" : "Wall Thickness", 
            "wall_thickness_tolerance" : "Wall Thickness Tolerance" 
        })
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
import panel as pn
import pandas as pd
from pathlib import Path
from apps.app_BOM_Management.BOM_Management import BOM_ManagementBackend
from shared.tdm_logging import logger, log_error, class_method_name

raw_css =[
    """
    label {
        position: relative;
        display: inline-block;
        &:before {
            content: '';
            height: ($height - 5) + px;
            position: absolute;
            right: 7px;
            top: 3px;
            width: 22px;

            //background: -webkit-linear-gradient(#fff, #f0f0f0);
            //background: -moz-linear-gradient(#fff, #f0f0f0);
            //background: linear-gradient(#f5f5f5, #e0e0e0);
            background: #fff; //for Firefox in Android

            border-top-right-radius: 3px;
            border-bottom-right-radius: 3px;
            pointer-events: none;
            display: block;
        }
        &:after {
            content: " ";
            position: absolute;
            right: 15px;
            top: 46%;
            margin-top: -3px;
            z-index: 2;
            pointer-events: none;
            width: 0;
            height: 0;
            border-style: solid;
            border-width: 6.9px 4px 0 4px;
            border-color: #aaa transparent transparent transparent;
            pointer-events: none;
        }
        select {
            -webkit-appearance: none;
            -moz-appearance: none;
            appearance: none;
            padding: 0 30px 0 10px;

            border: 1px solid #e0e0e0;
            border-radius: 3px;
            line-height: $height + px;
            height: $height + px;
            //box-shadow: inset 1px 1px 1px 0px rgba(0, 0, 0, 0.2);
            background: #fff;

            //min-width: 200px;
            margin: 0 5px 5px 0;
        }
        }
        //fix for ie 10 later
        select::-ms-expand {
        display: none;
        }
        """
]

pn.extension('tabulator',
             comms='default',
             loading_spinner='arcs',
             css_files=[pn.io.resources.CSS_URLS['font-awesome']],
             notifications=True,
             sizing_mode='stretch_width',
             template='material',
             safe_embed=True,
             dev=False,
             raw_css=raw_css,
             )

backend = BOM_ManagementBackend()

def BOM_Management_page():
    # Widgets
    insert_button = pn.widgets.Button(name="Insert into PostgreSQL", button_type="primary")
    update_button = pn.widgets.Button(name="Update selected row", button_type="success")
    delete_button = pn.widgets.Button(name="Delete selected row", button_type="danger")

    output_area = pn.pane.Markdown("", sizing_mode="stretch_width")
    search_box = pn.widgets.TextInput(name="Search", placeholder="Search Item ID or description...")

    # -----------------------
    # insert input
    manual_item_id = pn.widgets.TextInput(name="item_id", placeholder="Enter Item ID")
    manual_description = pn.widgets.TextInput(name="description", placeholder="Enter description")
    insert_manual_button = pn.widgets.Button(name="Insert Row", button_type="primary")
    manual_inputs = pn.Column(
        pn.pane.Markdown("### Add Item Manually"),
        manual_item_id,
        manual_description,
        insert_manual_button,
        visible=False
    )   

    # Data
    df_table = pd.DataFrame(columns=["item_id", "description"])
    table = pn.widgets.Tabulator(df_table, 
                                 pagination="local", 
                                 page_size=20,
                                 sizing_mode="stretch_width", 
                                 show_index=False,
                                 selectable=True)

    btn_table_csv_download = pn.widgets.FileDownload(backend.csv_download_callback(),
                                                     filename='BOM.csv',
                                                     auto=True,
                                                     embed=False,
                                                     button_style='outline',
                                                     button_type='success',
                                                     label='CSV',
                                                     height=32,
                                                     disabled=False
                                                     )
    
    btn_table_excel_download = pn.widgets.FileDownload(backend.excel_download_callback(),
                                                       filename='BOM.xlsx',
                                                       label='Excel',
                                                       embed=False,
                                                       button_style='outline',
                                                       button_type='success',
                                                       height=32,
                                                       disabled=False,
                                                       )
    
    # -----------------------
    # Insert Button: show insert Form
    def show_form(event):
        manual_inputs.visible = not manual_inputs.visible

    # -----------------------
    # Select Callback
    def select_data(event):
        rows = backend.fetch_data()
        if rows is not None and not rows.empty:
            table.value = pd.DataFrame(rows, columns=["item_id", "description"])
        else:
            table.value = pd.DataFrame(columns=["item_id", "description"])

    # -----------------------
    # Update Callback
    def update_row(event):
        if not table.selection:
            output_area.object = "### Plase select row for update"
            return

        row_index = table.selection[0]
        selected_row = table.value.iloc[row_index]

        item_id = selected_row["item_id"]
        new_description = selected_row["description"]

        msg = backend.update_bom_master_only(item_id, new_description)
        output_area.object = msg if msg else f"Updated {item_id} successfully"

    # -----------------------
    # Delete Callback
    def delete_row(event):
        if not table.selection:
            output_area.object = "### Plase select row for delete"
            return

        row_index = table.selection[0]
        selected_row = table.value.iloc[row_index]
        item_id = selected_row["item_id"]

        msg = backend.delete_bom_master_only(item_id)
        output_area.object = msg if msg else f"Deleted {item_id} successfully"

        # Remove row from UI table
        df = table.value.drop(index=row_index).reset_index(drop=True)
        table.value = df

    # -----------------------
    # insert Callback
    def insert_manual_data(event):
        item = manual_item_id.value.strip()
        desc = manual_description.value.strip()

        if not item or not desc:
            output_area.object = "Please fill in both Item ID and description."
            return

        # Append new row
        new_row = pd.DataFrame([[item, desc]], columns=["item_id", "description"])

        table.stream(new_row, follow=True)

        manual_item_id.value = ""
        manual_description.value = ""
        output_area.object = "Inserted new record manually."
        msg = backend.insert_into_bom_master(item, desc)
        output_area.object = f"Inserted into DB.\n\n**{msg}**"

    
    # -----------------------
    # search callback
    def filter_table(event):
        keyword = search_box.value.strip().lower()

        if keyword == "":
            select_data(None)
            return
        
        df = table.value
        filtered = df[
            df["item_id"].str.lower().str.contains(keyword) |
            df["description"].str.lower().str.contains(keyword)
        ]
        table.value = filtered

    # -----------------------
    # call function on click
    insert_button.on_click(show_form)
    update_button.on_click(update_row)
    delete_button.on_click(delete_row)
    insert_manual_button.on_click(insert_manual_data)
    search_box.param.watch(filter_table, "value")


    # Load custom template
    template_path = Path('apps/app_BOM_Management/templates/template_BOM_Management.html')
    template_str = template_path.read_text(encoding="utf-8")
    template = pn.Template(template=template_str)

    # Header
    header_html = "<h4 class='page-title mb-0'>BOM Management</h4>"
    template.add_panel('header', pn.Row(pn.pane.HTML(header_html)))

    # -----------------------
    # Extract controls
    controls_column = pn.Column(
        pn.Row(insert_button, update_button, delete_button),
        manual_inputs,
        search_box,
        output_area,
        table,
        sizing_mode="stretch_width",
    )
    template.add_panel('BOM_Management', controls_column)
    template.add_panel('xl_download', btn_table_excel_download)
    template.add_panel('csv_download', btn_table_csv_download)

    pn.state.onload(lambda: select_data(None))
    return template

# Serve the app
app = BOM_Management_page()
app.servable()

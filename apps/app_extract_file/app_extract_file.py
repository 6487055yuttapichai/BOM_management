import panel as pn
import pandas as pd
from pathlib import Path
import os
from apps.app_extract_file.extract_file import extract_file_backend

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

pn.extension('plotly', 'tabulator',
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

backend = extract_file_backend()

def extract_file_page():
    # Widgets
    file_input = pn.widgets.FileInput(accept=".txt")
    extract_button = pn.widgets.Button(name="Extracted data from file", button_type="warning")
    insert_button = pn.widgets.Button(name="Insert into PostgreSQL", button_type="primary")
    output_area = pn.pane.Markdown("", sizing_mode="stretch_width")
    keyword_input = pn.widgets.TextInput(name="Keyword", placeholder="Enter keyword (e.g. TUBING,PLASTIC)")

    match_switch = pn.widgets.Switch(name="Match with Database", value=True)

    
    table = pn.widgets.Tabulator(pd.DataFrame(columns=["Item ID", "Description", "Inv Unt", "Net Quantity"]), 
                                 pagination="local", page_size=20,
                                 sizing_mode="stretch_width", selectable=True)

    btn_table_csv_download = pn.widgets.FileDownload(filename='output.csv',
                                                     auto=True,
                                                     embed=False,
                                                     button_style='outline',
                                                     button_type='success',
                                                     label='CSV',
                                                     height=32,
                                                     disabled=False,
                                                     )
    
    def set_Download_file(value,csv_filename):
        btn_table_csv_download.file = backend.csv_download_callback(value)
        btn_table_csv_download.filename = csv_filename+".csv"


    def extract_data(event):
        if not file_input.value:
            output_area.object = "Please select a file first."
            return
        
        uploaded_filename = file_input.filename or "output"
        csv_filename = os.path.splitext(uploaded_filename)[0]
        backend.chassi = csv_filename
        
        
        keyword = keyword_input.value.strip()
        temp_path = "./temp_uploaded_file.txt"
        with open(temp_path, "wb") as f:
            f.write(file_input.value)

        data_list = backend.extract_tubing_with_item_number(temp_path,keyword)
        if match_switch.value:
            items_in_db = backend.Matching_file_with_DB(data_list)
            result_list = items_in_db
        else:
            result_list = data_list

        if result_list:
            df = pd.DataFrame(result_list, columns=["Item ID", "Description", "Inv Unt", "Net Quantity"])
            df["chassi"] = csv_filename
            set_Download_file(df,csv_filename)
            table.value = df
            
            output_area.object = f"Found {len(result_list)} record(s)"
        else:
            table.value = pd.DataFrame(columns=["Item ID", "Description", "Inv Unt", "Net Quantity","csv_filename"])
            output_area.object = "No {keyword} record found"

    extract_button.on_click(extract_data)

    def insert_data(event):
        if table.value.empty:
            output_area.object = "Don't have data"
            return
        data_to_insert = list(table.value.itertuples(index=False, name=None))
        msg = backend.insert_data_list_to_BOM_items(data_to_insert)
        output_area.object = f"\n\n**{msg}**"

    insert_button.on_click(insert_data)
    

    # Load custom template
    template_path = Path('apps/app_extract_file/templates/template_extract_file.html')
    template_str = template_path.read_text(encoding="utf-8")
    template = pn.Template(template=template_str)

    # Header
    header_html = "<h4 class='page-title mb-0'>Extract File Page</h4>"
    template.add_panel('header', pn.Row(pn.pane.HTML(header_html)))

    # Extract controls
    controls_column = pn.Column(
        file_input,
        keyword_input,
        match_switch,
        pn.Row(extract_button, insert_button),
        output_area,
        table,
        sizing_mode='stretch_both'
    )
    template.add_panel('extract_controls', controls_column)
    template.add_panel('csv_download', btn_table_csv_download)

    return template

# Serve the app
app = extract_file_page()
app.servable()

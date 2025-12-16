import panel as pn
import pandas as pd
from pathlib import Path
from apps.Monitor_folder_by_page.Monitor_folder_by_page import Monitor_folder_backend
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

backend = Monitor_folder_backend()

def Monitor_folder_page():
    # Load custom template
    template_path = Path('apps/Monitor_folder_by_page/templates/template_Monitor_folder.html')
    template_str = template_path.read_text(encoding="utf-8")
    template = pn.Template(template=template_str)

    # Header
    header_html = "<h4 class='page-title mb-0'>Monitor folder</h4>"
    template.add_panel('header', pn.Row(pn.pane.HTML(header_html)))

    Monitor_folder = pn.Column(
        backend.btn_refresh,
        pn.Row(
            pn.Column(
                backend.input_select,
                backend.upload_input,
                backend.btn_upload,
                backend.btn_delete_input,
            ),
            pn.Column(
                backend.output_select,
                backend.btn_download_all,
                backend.btn_download_output,
                backend.btn_delete_output,
            ),
        ),
        sizing_mode="stretch_width",
    )
    template.add_panel('Monitor_folder', Monitor_folder)

    return template

app = Monitor_folder_page()
app.servable()

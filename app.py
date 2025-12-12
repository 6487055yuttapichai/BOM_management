from pathlib import Path
import panel as pn

from apps.app_BOM_Management.app_BOM_Management import BOM_Management_page
from apps.app_extract_file.app_extract_file import extract_file_page

pn.extension()

ROUTES = {
    "BOM_Managementpy": BOM_Management_page,
    "extract_file_page": extract_file_page,
}

pn.serve(ROUTES,
         port=5006,
         allow_websocket_origin=["*"],
         show=False,
         admin=False,
         log_level="info",
         num_threads=4,
         ico_path=Path(__file__).parent / "assets" / "img" / "favicon.ico",
         static_dirs={'assets': Path(__file__).parent / "assets"},
         reuse_sessions=True,
         global_loading_spinner=False)

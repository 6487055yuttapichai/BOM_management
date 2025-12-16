from pathlib import Path
import panel as pn
import threading

from apps.TXT_to_CSV.watchdog_service import start_watchdog
from apps.app_BOM_Management.app_BOM_Management import BOM_Management_page
from apps.Monitor_folder_by_page.app_Monitor_folder_by_page import Monitor_folder_page
pn.extension()

ROUTES = {
    "Monitor_folder": Monitor_folder_page,
    "BOM_Management": BOM_Management_page,
}

# ===== START WATCHDOG =====
watchdog_thread = threading.Thread(
    target=start_watchdog,
    daemon=True
)
watchdog_thread.start()


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

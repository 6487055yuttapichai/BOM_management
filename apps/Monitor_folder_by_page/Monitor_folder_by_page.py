import zipfile
from pathlib import Path
import panel as pn


class Monitor_folder_backend:
    def __init__(self):
        # ===== CONFIG =====
        self.INPUT_DIR = Path("apps/TXT_to_CSV/input_file")
        self.OUTPUT_DIR = Path("apps/TXT_to_CSV/output_file")

        self.INPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # ===== WIDGETS =====
        self.input_select = pn.widgets.Select(
            name="📂 Input TXT Files",
            options=[],
            size=10
        )

        self.output_select = pn.widgets.Select(
            name="📂 Output CSV Files",
            options=[],
            size=10
        )

        self.upload_input = pn.widgets.FileInput(
            accept=".txt",
            multiple=True
        )

        self.btn_upload = pn.widgets.Button(
            name="⬆ Upload",
            button_type="primary"
        )

        self.btn_delete_input = pn.widgets.Button(
            name="🗑 Delete Input",
            button_type="danger"
        )

        self.btn_delete_output = pn.widgets.Button(
            name="🗑 Delete Output",
            button_type="danger"
        )

        self.btn_download_output = pn.widgets.FileDownload(
            label="⬇ Download Output",
            button_type="success",
            auto=True,
            disabled = True
        )

        self.btn_download_all = pn.widgets.FileDownload(
            label="⬇ Download All Output",
            button_type="success",
            button_style="outline",
            auto=True,
            disabled=True
        )

        self.btn_refresh = pn.widgets.Button(
            name="🔄 Refresh",
            button_type="primary"
        )

        self.btn_refresh.on_click(self.refresh_all)
        self.btn_upload.on_click(self.upload_files)
        self.btn_delete_input.on_click(self.delete_input)
        self.btn_delete_output.on_click(self.delete_output)
        self.output_select.param.watch(
            self.update_download_button,
            "value"
        )
        self.btn_download_all.callback = self.download_all_outputs

        # initial load
        self.refresh_all()

    # ===== UTILS FILE=====
    def get_files(self, folder, suffix=None):
        files = folder.glob(f"*{suffix}") if suffix else folder.iterdir()
        return sorted([f.name for f in files if f.is_file()])

    # ===== LOGIC FILE =====
    def refresh_all(self, event=None):
        self.input_select.options = []
        self.output_select.options = []

        self.input_select.options = self.get_files(self.INPUT_DIR, ".txt")
        self.output_select.options = self.get_files(self.OUTPUT_DIR, ".csv")

        self.btn_download_all.disabled = len(self.output_select.options) == 0

    def upload_files(self, event=None):
        if not self.upload_input.value:
            return

        for filename, content in zip(
            self.upload_input.filename,
            self.upload_input.value
        ):
            with open(self.INPUT_DIR / filename, "wb") as f:
                f.write(content)

        self.upload_input.value = None
        self.refresh_all()

    def delete_input(self, event=None):
        if self.input_select.value:
            path = self.INPUT_DIR / self.input_select.value
            if path.exists():
                path.unlink()
        self.refresh_all()

    def delete_output(self, event=None):
        if self.output_select.value:
            path = self.OUTPUT_DIR / self.output_select.value
            if path.exists():
                path.unlink()
        self.refresh_all()

    def update_download_button(self, event=None):
        if not self.output_select.value:
            self.btn_download_output.disabled = True
            return

        file_path = self.OUTPUT_DIR / self.output_select.value
        if file_path.exists():
            self.btn_download_output.file = file_path
            self.btn_download_output.filename = file_path.name
            self.btn_download_output.disabled = False

    def download_all_outputs(self):
        csv_files = list(self.OUTPUT_DIR.glob("*.csv"))
        if not csv_files:
            self.btn_download_all.disabled = True
            return

        zip_path = self.OUTPUT_DIR / "output_all.zip"

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in csv_files:
                zf.write(file, arcname=file.name)

        self.btn_download_all.file = zip_path
        self.btn_download_all.filename = "output_all.zip"
        self.btn_download_all.disabled = False

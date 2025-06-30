# ui/conversion_viewer.py
import os
import datetime
import subprocess
from PIL import Image
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QHBoxLayout, QMessageBox
)
from PySide6.QtCore import Qt

SUPPORTED_IMAGE_FORMATS = [".jpg", ".jpeg", ".png", ".heic"]
SUPPORTED_VIDEO_FORMATS = [".mp4", ".mov", ".avi", ".mkv"]

def convert_image(input_path, output_format="jpg", strip_metadata=False):
    try:
        output_path = os.path.abspath(os.path.splitext(input_path)[0] + f"_converted.{output_format}")
        with Image.open(input_path) as img:
            if img.mode in ("RGBA", "LA"):
                img = img.convert("RGB")

            if strip_metadata:
                data = list(img.getdata())
                img_no_meta = Image.new(img.mode, img.size)
                img_no_meta.putdata(data)
                img_no_meta.save(output_path)
            else:
                img.save(output_path)

        return output_path if os.path.exists(output_path) else None
    except Exception as e:
        return f"Image conversion error: {e}"

def convert_video(input_path, output_format="mp4", strip_metadata=False, custom_metadata=None):
    try:
        output_path = os.path.abspath(os.path.splitext(input_path)[0] + f"_converted.{output_format}")
        cmd = ["ffmpeg", "-y", "-i", input_path]

        if strip_metadata:
            cmd += ["-map_metadata", "-1"]
        elif custom_metadata:
            for k, v in custom_metadata.items():
                cmd += ["-metadata", f"{k}={v}"]

        cmd += ["-c:v", "libx264", "-preset", "fast", "-crf", "23", "-c:a", "aac", "-b:a", "128k", output_path]
        subprocess.run(cmd, check=True)
        return output_path if os.path.exists(output_path) else None
    except subprocess.CalledProcessError as e:
        return f"FFmpeg error: {e}"
    except Exception as e:
        return f"Video conversion error: {e}"

def batch_convert_folder(folder_path, output_format):
    results = []
    output_ext = f".{output_format.lower()}"

    for filename in os.listdir(folder_path):
        full_path = os.path.join(folder_path, filename)
        name, ext = os.path.splitext(filename)

        if ext.lower() not in SUPPORTED_IMAGE_FORMATS + SUPPORTED_VIDEO_FORMATS:
            continue
        if name.endswith("_converted"):
            continue

        if ext.lower() in SUPPORTED_IMAGE_FORMATS:
            result = convert_image(full_path, output_format)
        else:
            result = convert_video(full_path, output_format)

        if isinstance(result, str) and result.endswith(output_ext):
            results.append({"result": result})
        else:
            print(f"❌ Failed conversion for: {filename} -> {result}")
            results.append({"error": result})

    return results

class ConversionBrowser(QWidget):
    def __init__(self, go_back_callback=None):
        super().__init__()
        self.go_back_callback = go_back_callback
        self.setMinimumSize(1300, 900)
        self.setWindowTitle("🌀 Bulk File Format Converter")

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        self.setLayout(layout)


        # --- Top Bar ---
        top_bar = QHBoxLayout()
        if self.go_back_callback:
            back_btn = QPushButton("← Back")
            back_btn.setFixedSize(100, 40)
            back_btn.clicked.connect(self.go_back_callback)
            top_bar.addWidget(back_btn)

        self.folder_btn = QPushButton("📁 Import Folder")
        self.folder_btn.setFixedSize(140, 40)
        self.folder_btn.clicked.connect(self.import_folder)
        top_bar.addWidget(self.folder_btn)

        self.format_dropdown = QComboBox()
        self.format_dropdown.setFixedSize(140, 40)
        self.format_dropdown.addItem("Select output format")
        for fmt in SUPPORTED_IMAGE_FORMATS + SUPPORTED_VIDEO_FORMATS:
            self.format_dropdown.addItem(fmt.lstrip("."))
        top_bar.addWidget(self.format_dropdown)

        self.convert_btn = QPushButton("🔁 Convert")
        self.convert_btn.setFixedSize(100, 40)
        self.convert_btn.clicked.connect(self.run_bulk_conversion)
        top_bar.addWidget(self.convert_btn)

        self.download_all_btn = QPushButton("⬇️ Download All")
        self.download_all_btn.setFixedSize(140, 40)
        self.download_all_btn.clicked.connect(self.download_all_files)
        top_bar.addWidget(self.download_all_btn)

        top_bar.addStretch()
        layout.addLayout(top_bar)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["File Name", "File Type", "Size (MB)", "Date Modified", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        self.folder_path = None
        self.converted_file_paths = []

    def import_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.folder_path = folder_path
            self.table.setRowCount(0)
            self.converted_file_paths = []

            for entry in os.listdir(folder_path):
                full_path = os.path.join(folder_path, entry)
                if not os.path.isfile(full_path):
                    continue

                ext = os.path.splitext(entry)[1].lower()
                if ext not in SUPPORTED_IMAGE_FORMATS + SUPPORTED_VIDEO_FORMATS:
                    continue

                file_info = os.stat(full_path)
                file_name = os.path.basename(full_path)
                file_type = ext.lstrip(".")
                file_size = f"{file_info.st_size / (1024 * 1024):.2f}"
                modified = datetime.datetime.fromtimestamp(file_info.st_mtime).strftime("%Y-%m-%d %H:%M:%S")

                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(file_name))
                self.table.setItem(row, 1, QTableWidgetItem(file_type))
                self.table.setItem(row, 2, QTableWidgetItem(file_size))
                self.table.setItem(row, 3, QTableWidgetItem(modified))
                self.table.setItem(row, 4, QTableWidgetItem("Pending"))

            # QMessageBox.information(self, "Folder Selected", f"Imported: {folder_path}")

    def run_bulk_conversion(self):
        if not self.folder_path:
            QMessageBox.warning(self, "No Folder", "Please select a folder first.")
            return

        output_format = self.format_dropdown.currentText().strip()
        if output_format == "Select output format":
            QMessageBox.warning(self, "No Format", "Please select an output format.")
            return

        results = batch_convert_folder(self.folder_path, output_format)

        self.converted_file_paths = []
        self.table.setRowCount(0)

        row = 0
        for result in results:
            if "result" in result:
                file_path = result["result"]
                if os.path.isfile(file_path):
                    self.converted_file_paths.append(file_path)
                    file_info = os.stat(file_path)
                    file_name = os.path.basename(file_path)
                    file_type = os.path.splitext(file_name)[1].lstrip(".")
                    file_size = f"{file_info.st_size / (1024 * 1024):.2f}"
                    modified = datetime.datetime.fromtimestamp(file_info.st_mtime).strftime("%Y-%m-%d %H:%M:%S")

                    self.table.insertRow(row)
                    self.table.setItem(row, 0, QTableWidgetItem(file_name))
                    self.table.setItem(row, 1, QTableWidgetItem(file_type))
                    self.table.setItem(row, 2, QTableWidgetItem(file_size))
                    self.table.setItem(row, 3, QTableWidgetItem(modified))

                    download_btn = QPushButton("Download")
                    download_btn.clicked.connect(lambda _, path=file_path: os.startfile(path))
                    self.table.setCellWidget(row, 4, download_btn)

                    row += 1

            elif "error" in result:
                print(f"❌ Conversion error: {result['error']}")

        if not self.converted_file_paths:
            QMessageBox.information(self, "Conversion Complete", "No valid files converted.")
        else:
            QMessageBox.information(self, "Success", f"{len(self.converted_file_paths)} file(s) converted.")

    def download_all_files(self):
        if not self.converted_file_paths:
            QMessageBox.warning(self, "No Files", "There are no converted files to download.")
            return

        output_dir = os.path.dirname(self.converted_file_paths[0])
        try:
            os.startfile(output_dir)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open folder:\n{e}")

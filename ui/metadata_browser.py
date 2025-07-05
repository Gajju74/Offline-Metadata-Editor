from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFileDialog, QTableWidget, QTableWidgetItem,
    QLabel, QHeaderView, QHBoxLayout, QMessageBox, QCheckBox, QDialog, QScrollArea,
    QFormLayout, QLineEdit, QDateTimeEdit
)
from PySide6.QtCore import Qt, QDateTime
import os
import mimetypes
import subprocess
import re
import json
from datetime import datetime

# Helper function to read metadata using exiftool for any file type
def read_metadata_with_exiftool(file_path):
    """
    Reads metadata from a file using exiftool and returns it as a dictionary.
    Excludes 'SourceFile' and strips group prefixes (e.g., 'ExifIFD:') from keys.
    Handles cases where exiftool finds no metadata gracefully, returning 'Info'.
    """
    try:
        # Use -json to get output in JSON format
        # -G1 includes group names like 'ExifIFD:Make', which we'll strip
        # Set check=False to prevent CalledProcessError for non-zero exit codes (e.g., no metadata)
        process = subprocess.run(
            ["exiftool", "-json", "-G1", file_path],
            capture_output=True, text=True, check=False, encoding='utf-8', errors='ignore'
        )

        if process.returncode != 0:
            # Exiftool returned a non-zero exit code.
            # Check if it's due to no metadata found, or a real error.
            stderr_output = process.stderr.strip().lower()
            if "no exif data" in stderr_output or "no data found" in stderr_output or "no source files" in stderr_output or not stderr_output:
                # Treat as no metadata found, not a critical error
                return {"Info": f"No relevant metadata found for {os.path.basename(file_path)}."}
            else:
                # It's a real error from exiftool
                return {"Error": f"Exiftool process failed for {os.path.basename(file_path)}: {process.stderr.strip()}"}
        
        # If returncode is 0, proceed with JSON parsing
        metadata_list = json.loads(process.stdout)
        if metadata_list:
            metadata = metadata_list[0] # exiftool -json outputs a list, even for a single file
            
            cleaned_metadata = {}
            for key, value in metadata.items():
                if key == 'SourceFile':
                    continue
                clean_key = re.sub(r'^[A-Za-z0-9_]+:', '', key)
                cleaned_metadata[clean_key] = value
            return cleaned_metadata
        else:
            # This case might happen if exiftool runs successfully (exit code 0) but produces empty JSON
            return {"Info": f"No metadata found for {os.path.basename(file_path)}."}

    except FileNotFoundError:
        return {"Error": "Exiftool not found. Please ensure it's installed and in your PATH."}
    except json.JSONDecodeError:
        return {"Error": f"Failed to parse Exiftool JSON output for {os.path.basename(file_path)}. Is the file corrupted or not a recognized type?"}
    except Exception as e:
        return {"Error": f"An unexpected error occurred during metadata reading for {os.path.basename(file_path)}: {e}"}

class NoScrollDateTimeEdit(QDateTimeEdit):
    def wheelEvent(self, event):
        event.ignore()

class MetadataViewer(QDialog):
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Metadata Viewer & Editor")
        self.setMinimumSize(1280, 720)

        self.file_path = file_path
        self.metadata = self.load_metadata()
        self.field_widgets = {}
        
        layout = QVBoxLayout()
        self.setLayout(layout)

        heading = QLabel("Metadata Editor")
        heading.setAlignment(Qt.AlignCenter)
        heading.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 25px;
            color: #66afe9;
            padding-top: 10px;
        """)
        layout.addWidget(heading)


        # Top Bar
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel(f"File: {os.path.basename(file_path)}"))
        top_bar.addStretch()

        copy_btn = QPushButton("\ud83d\udccb Copy Metadata")
        copy_btn.clicked.connect(self.copy_metadata_to_other_file)
        top_bar.addWidget(copy_btn)

        import_btn = QPushButton("\ud83d\udce5 Import Metadata (TXT)")
        import_btn.clicked.connect(self.import_metadata_from_txt)
        top_bar.addWidget(import_btn)

        layout.addLayout(top_bar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        self.form_layout = QFormLayout()
        container.setLayout(self.form_layout)
        scroll.setWidget(container)
        layout.addWidget(scroll)

        self.populate_fields()

        save_button = QPushButton("\ud83d\udcbe Save Metadata")
        save_button.clicked.connect(self.save_metadata)
        layout.addWidget(save_button)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

    def load_metadata(self):
        # Now uses the generic exiftool reader
        return read_metadata_with_exiftool(self.file_path)

    def populate_fields(self):
        # Clear existing fields to avoid duplication when reloading
        for i in reversed(range(self.form_layout.count())): 
            widget_item = self.form_layout.itemAt(i)
            if widget_item is not None:
                widget = widget_item.widget()
                if widget is not None:
                    widget.setParent(None) # Remove the widget from layout and delete it

        self.field_widgets = {} # Clear the dictionary

        for key, value in self.metadata.items():
            # Skip error/info messages from exiftool reading for field editing
            if key in ["Error", "Info"]:
                self.form_layout.addRow(QLabel(key), QLabel(str(value)))
                continue

            label = QLabel(key)
            if "Date" in key and isinstance(value, str):
                field = NoScrollDateTimeEdit()
                field.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
                # Try multiple date formats for robustness
                dt = QDateTime.fromString(value, "yyyy-MM-dd HH:mm:ss")
                if not dt.isValid():
                    dt = QDateTime.fromString(value, "yyyy:MM:dd HH:mm:ss")
                if not dt.isValid():
                    dt = QDateTime.fromString(value, "yyyy:MM:dd hh:mm:ss") # Common ExifTool format
                if not dt.isValid():
                    dt = QDateTime.currentDateTime() # Fallback
                field.setDateTime(dt)
                self.form_layout.addRow(label, field)
                self.field_widgets[key] = field
            elif isinstance(value, (int, float, str)):
                field = QLineEdit(str(value))
                # Make certain fields non-editable (e.g., computed values by exiftool)
                if key.lower() in ["file name", "file size", "directory", "file type", "mimetype", "sourcefile"]:
                    field.setReadOnly(True)
                    field.setStyleSheet("background-color: #333; color: #aaa;")
                self.form_layout.addRow(label, field)
                self.field_widgets[key] = field

    def save_metadata(self):
        args = ["exiftool", "-overwrite_original"]
        for key, widget in self.field_widgets.items():
            # Skip keys that are display-only or internal to exiftool output
            if key.lower() in ["file name", "file size", "directory", "file type", "mimetype", "sourcefile", "error", "info"]:
                continue
            
            # Ensure the key is formatted correctly for exiftool (no spaces, for example)
            exif_key = key.replace(" ", "")

            val = ""
            if isinstance(widget, QLineEdit):
                if not widget.isReadOnly(): # Only save if editable
                    val = widget.text()
            elif isinstance(widget, QDateTimeEdit):
                val = widget.dateTime().toString("yyyy:MM:dd HH:mm:ss")
            
            if val: # Only add argument if there's a value to set
                args.append(f"-{exif_key}={val}")
                
        args.append(self.file_path)
        try:
            # Check if there are actual changes to apply beyond the file path
            if len(args) > 2: # exiftool, -overwrite_original, file_path
                subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                QMessageBox.information(self, "Success", "Metadata saved successfully.")
                self.metadata = self.load_metadata() # Reload metadata to reflect changes
                self.populate_fields() # Repopulate fields
            else:
                QMessageBox.information(self, "No Changes", "No editable metadata fields were modified.")
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Error", f"Failed to save metadata:\n{e.stderr.decode()}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred during save: {e}")

    def copy_metadata_to_other_file(self):
        target_file, _ = QFileDialog.getOpenFileName(self, "Select Target File")
        if not target_file:
            return
        try:
            # Metadata is now copied directly from the source file using exiftool's tagsFromFile
            subprocess.run(["exiftool", "-overwrite_original", f"-tagsFromFile={self.file_path}", target_file],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            QMessageBox.information(self, "Copied", f"Metadata copied to:\n{os.path.basename(target_file)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to copy metadata: {e}")

    def import_metadata_from_txt(self):
        txt_file, _ = QFileDialog.getOpenFileName(self, "Select Metadata TXT File", "", "Text Files (*.txt)")
        if not txt_file:
            return
        args = ["exiftool", "-overwrite_original"]
        try:
            with open(txt_file, "r", encoding="utf-8") as f:
                for line in f:
                    if ":" not in line:
                        continue
                    match = re.match(r"^(.*?):\s*(.*)$", line.strip())
                    if not match:
                        continue
                    # Ensure key is formatted for exiftool (no spaces), handle values
                    key, val = match.group(1).strip().replace(" ", ""), match.group(2).strip()
                    # Skip common exiftool computed tags
                    if key.lower() not in ["filename", "filesize", "error", "warning", "directory", "filetype", "mimetype", "sourcefile", "info"]:
                        args.append(f"-{key}={val}")
            args.append(self.file_path)
            
            if len(args) > 2: # Check if there are actual tags to import
                subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                QMessageBox.information(self, "Imported", "Metadata imported successfully from TXT.")
                self.metadata = self.load_metadata() # Reload metadata to reflect changes
                self.populate_fields() # Repopulate fields
            else:
                QMessageBox.information(self, "No Data", "No valid metadata tags found in the TXT file to import.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

class MetadataBrowser(QWidget):
    def __init__(self, go_back_callback=None):
        super().__init__()
        self.go_back_callback = go_back_callback
        self.setMinimumSize(1300, 900)
        self.setWindowTitle("\ud83d\udcc1 Folder Import – Offline Metadata Editor")

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        self.setLayout(layout)

        # --- Main Heading for MetadataBrowser ---
        main_heading = QLabel("Metadata Editor")
        main_heading.setAlignment(Qt.AlignCenter)
        main_heading.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 25px;
            color: #66afe9;
            padding-top: 10px;
        """)
        layout.addWidget(main_heading)
        # --- End Main Heading ---

        header_layout = QHBoxLayout()
        if self.go_back_callback:
            back_button = QPushButton("\u2190 Back")
            back_button.setFixedSize(80, 35)
            back_button.clicked.connect(self.go_back_callback)
            header_layout.addWidget(back_button)

        self.import_button = QPushButton("\ud83d\udcc1 Import Folder")
        self.import_button.setFixedHeight(40)
        self.import_button.clicked.connect(self.import_folder)

        # New Select All/Unselect All buttons
        self.select_all_button = QPushButton("✅ Select All")
        self.select_all_button.setFixedHeight(40)
        self.select_all_button.clicked.connect(self.select_all_files)
        header_layout.addWidget(self.select_all_button)

        self.unselect_all_button = QPushButton("⬜ Unselect All")
        self.unselect_all_button.setFixedHeight(40)
        self.unselect_all_button.clicked.connect(self.unselect_all_files)
        header_layout.addWidget(self.unselect_all_button)

        self.export_button = QPushButton("\ud83d\udec4 Export Metadata (TXT)")
        self.export_button.setFixedHeight(40)
        self.export_button.clicked.connect(self.export_selected_metadata)

        self.delete_button = QPushButton("\ud83d\uddd1 Delete Metadata")
        self.delete_button.setFixedHeight(40)
        self.delete_button.clicked.connect(self.delete_selected_metadata)

        self.refresh_button = QPushButton("\ud83d\udd04 Refresh")
        self.refresh_button.setFixedHeight(40)
        self.refresh_button.clicked.connect(self.refresh_folder)

        self.folder_label = QLabel("No folder selected")
        self.folder_label.setStyleSheet("font-weight: bold; font-size: 16px; padding-left: 15px;")

        header_layout.addWidget(self.import_button)
        header_layout.addWidget(self.export_button)
        header_layout.addWidget(self.delete_button)
        header_layout.addWidget(self.refresh_button)
        header_layout.addWidget(self.folder_label)
        header_layout.addStretch()

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["File Name", "File Type", "Size (MB)", "Date Modified", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)

        layout.addLayout(header_layout)
        layout.addWidget(self.table)

    def import_folder(self, folder_path=None):
        folder = folder_path or QFileDialog.getExistingDirectory(self, "Select Folder")
        if not folder:
            return

        self.folder_label.setText(f"Imported: {folder}")
        self.table.setRowCount(0)

        # Iterate recursively through the selected folder
        for root, _, files in os.walk(folder):
            for entry in files:
                full_path = os.path.join(root, entry)
                
                # Try to get metadata for all files, no extension filtering
                metadata_result = read_metadata_with_exiftool(full_path)
                
                # Check for critical errors from exiftool
                if "Error" in metadata_result:
                    print(f"Skipping {full_path}: {metadata_result['Error']}")
                    continue # Skip to next file if metadata couldn't be read due to a critical error

                # Files with "Info" (no metadata found) or actual metadata will proceed
                size_mb = os.path.getsize(full_path) / (1024 * 1024)
                modified = datetime.fromtimestamp(os.path.getmtime(full_path)).strftime("%Y-%m-%d %H:%M:%S")
                
                # Use FileType from metadata_result if available, otherwise guess MIME type, then fall back to extension
                file_type = metadata_result.get('FileType', mimetypes.guess_type(full_path)[0])
                if not file_type: # if mimetypes.guess_type returns None
                    file_type = os.path.splitext(entry)[1] # Use extension as fallback
                
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setRowHeight(row, 30)

                checkbox = QCheckBox(entry)
                checkbox.setProperty("file_path", full_path)
                self.table.setCellWidget(row, 0, checkbox)
                self.table.setItem(row, 1, self._non_editable_item(file_type))
                self.table.setItem(row, 2, self._non_editable_item(f"{size_mb:.2f}"))
                self.table.setItem(row, 3, self._non_editable_item(modified))

                btn = QPushButton("View/Edit")
                btn.setProperty("file_path", full_path)
                btn.clicked.connect(self.handle_view_edit_click)
                self.table.setCellWidget(row, 4, btn)

    def handle_view_edit_click(self):
        file_path = self.sender().property("file_path")
        viewer = MetadataViewer(file_path, self)
        viewer.exec()

    def refresh_folder(self):
        current = self.folder_label.text()
        if current.startswith("Imported: "):
            self.import_folder(current.replace("Imported: ", ""))

    def export_selected_metadata(self):
        exported = 0
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if not isinstance(checkbox, QCheckBox) or not checkbox.isChecked():
                continue
            path = checkbox.property("file_path")
            # Use the generic exiftool reader
            metadata = read_metadata_with_exiftool(path)
            
            if "Error" in metadata:
                print(f"❌ Failed to export metadata for {os.path.basename(path)}: {metadata['Error']}")
                QMessageBox.warning(self, "Export Error", f"Failed to export metadata for {os.path.basename(path)}:\n{metadata['Error']}")
                continue # Skip to next file if metadata couldn't be read due to a critical error

            try:
                with open(os.path.splitext(path)[0] + ".txt", "w", encoding="utf-8") as f:
                    for k, v in metadata.items():
                        # Exclude some internal exiftool fields that might not be useful in TXT export
                        if k.lower() not in ["sourcefile", "error", "info"]:
                            f.write(f"{k}: {v}\n")
                exported += 1
            except Exception as e:
                print(f"❌ Failed to export {os.path.basename(path)}: {e}")
                QMessageBox.critical(self, "Export Error", f"Failed to export {os.path.basename(path)}:\n{e}")

        QMessageBox.information(self, "Export", f"Exported metadata for {exported} file(s)." if exported else "No files selected.")

    def delete_selected_metadata(self):
        deleted = 0
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if not isinstance(checkbox, QCheckBox) or not checkbox.isChecked():
                continue
            path = checkbox.property("file_path")
            try:
                subprocess.run(["exiftool", "-overwrite_original", "-all=", path],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                deleted += 1
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to delete metadata for {os.path.basename(path)}: {e.stderr.decode()}")
                QMessageBox.warning(self, "Deletion Error", f"Failed to delete metadata for {os.path.basename(path)}:\n{e.stderr.decode()}")
        QMessageBox.information(self, "Deleted", f"Deleted metadata for {deleted} file(s)." if deleted else "No files selected.")

    def _non_editable_item(self, value):
        item = QTableWidgetItem(str(value))
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        return item

    def select_all_files(self):
        """Checks all checkboxes in the file list table."""
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if isinstance(checkbox, QCheckBox):
                checkbox.setChecked(True)

    def unselect_all_files(self):
        """Unchecks all checkboxes in the file list table."""
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if isinstance(checkbox, QCheckBox):
                checkbox.setChecked(False)
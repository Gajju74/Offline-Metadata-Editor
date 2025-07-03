import os
import mimetypes
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QCheckBox,
    QLineEdit, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal 

class BatchRenamerBrowser(QWidget):
    def __init__(self, go_back_callback=None):
        super().__init__()
        self.go_back_callback = go_back_callback
        self.current_folder = None

        self.setWindowTitle("Batch File Renamer")
        self.setMinimumSize(1300, 900)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        self.setLayout(layout)

        # --- Main Heading ---
        heading = QLabel("Batch File Renamer")
        heading.setAlignment(Qt.AlignCenter)
        heading.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 25px;
            color: #66afe9;
            padding-top: 10px;
        """)
        layout.addWidget(heading)

        # --- Header Layout (Back Button, Import Folder, Refresh) ---
        header_layout = QHBoxLayout()

        if self.go_back_callback:
            back_button = QPushButton("← Back")
            back_button.setFixedSize(80, 35)
            back_button.clicked.connect(self.go_back_callback)
            header_layout.addWidget(back_button)
        
        self.import_button = QPushButton("📁 Import Folder")
        self.import_button.setFixedHeight(40)
        self.import_button.clicked.connect(self.import_folder)
        header_layout.addWidget(self.import_button)

        self.refresh_button = QPushButton("🔄 Refresh")
        self.refresh_button.setFixedHeight(40)
        self.refresh_button.clicked.connect(self.refresh_folder)
        header_layout.addWidget(self.refresh_button)

        self.folder_label = QLabel("No folder selected")
        self.folder_label.setStyleSheet("font-weight: bold; font-size: 16px; padding-left: 15px;")
        header_layout.addWidget(self.folder_label)
        header_layout.addStretch() 

        layout.addLayout(header_layout)

        # --- File Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Select", "Type", "Size (MB)", "Modified"]) 
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        # --- New Select/Unselect All Buttons ---
        selection_buttons_layout = QHBoxLayout()
        self.select_all_button = QPushButton("✅ Select All Files")
        self.select_all_button.setFixedHeight(35) # Restore original height
        self.select_all_button.setMaximumWidth(180) # Limit maximum width
        self.select_all_button.clicked.connect(self.select_all_files)
        selection_buttons_layout.addWidget(self.select_all_button)

        self.unselect_all_button = QPushButton("❌ Unselect All Files")
        self.unselect_all_button.setFixedHeight(35) # Restore original height
        self.unselect_all_button.setMaximumWidth(180) # Limit maximum width
        self.unselect_all_button.clicked.connect(self.unselect_all_files)
        selection_buttons_layout.addWidget(self.unselect_all_button)
        selection_buttons_layout.addStretch() # Push buttons to the left
        layout.addLayout(selection_buttons_layout)


        # --- Renaming Options ---
        rename_controls_layout = QVBoxLayout()
        rename_controls_layout.setSpacing(10)

        # Prefix input and buttons
        prefix_layout = QHBoxLayout()
        prefix_layout.addWidget(QLabel("Prefix Text:"))
        self.prefix_input = QLineEdit()
        self.prefix_input.setPlaceholderText("Enter text to add or remove from beginning...")
        prefix_layout.addWidget(self.prefix_input)
        
        self.remove_prefix_button = QPushButton("🗑️ Remove Prefix")
        self.remove_prefix_button.setFixedSize(140, 35)
        self.remove_prefix_button.setStyleSheet("""
            QPushButton {
                background-color: #D32F2F;
                color: white;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #E53935;
            }
        """)
        self.remove_prefix_button.clicked.connect(self.remove_prefix_from_files)
        prefix_layout.addWidget(self.remove_prefix_button)

        rename_controls_layout.addLayout(prefix_layout)

        # Suffix input and buttons
        suffix_layout = QHBoxLayout()
        suffix_layout.addWidget(QLabel("Suffix Text:"))
        self.suffix_input = QLineEdit()
        self.suffix_input.setPlaceholderText("Enter text to add or remove from end...")
        suffix_layout.addWidget(self.suffix_input)

        self.remove_suffix_button = QPushButton("🗑️ Remove Suffix")
        self.remove_suffix_button.setFixedSize(140, 35)
        self.remove_suffix_button.setStyleSheet("""
            QPushButton {
                background-color: #D32F2F;
                color: white;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #E53935;
            }
        """)
        self.remove_suffix_button.clicked.connect(self.remove_suffix_from_files)
        suffix_layout.addWidget(self.remove_suffix_button)

        rename_controls_layout.addLayout(suffix_layout)

        # Main Rename (Add) Button
        self.rename_button = QPushButton("✨ Add Prefix/Suffix to Selected Files")
        self.rename_button.setFixedHeight(45) # Restored original height for this button
        self.rename_button.setStyleSheet("""
            QPushButton {
                background-color: #2E7D32;
                color: white;
                font-weight: bold;
                border-radius: 8px;
                font-size: 18px; /* Original font size that fit the 45px height */
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #aaa;
            }
        """)
        self.rename_button.clicked.connect(self.perform_add_rename)
        rename_controls_layout.addWidget(self.rename_button)

        layout.addLayout(rename_controls_layout)

        layout.addItem(QSpacerItem(0, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def import_folder(self, folder_path=None):
        folder = folder_path or QFileDialog.getExistingDirectory(self, "Select Folder")
        if not folder:
            return

        self.current_folder = folder
        self.folder_label.setText(f"Imported: {folder}")
        self.table.setRowCount(0)

        for entry in os.listdir(folder):
            full_path = os.path.join(folder, entry)
            if not os.path.isfile(full_path):
                continue

            size_mb = os.path.getsize(full_path) / (1024 * 1024)
            modified = datetime.fromtimestamp(os.path.getmtime(full_path)).strftime("%Y-%m-%d %H:%M:%S")
            mime_type, _ = mimetypes.guess_type(full_path)

            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setRowHeight(row, 30)

            checkbox = QCheckBox(entry)
            checkbox.setProperty("file_path", full_path) 
            self.table.setCellWidget(row, 0, checkbox)
            
            self.table.setItem(row, 1, self._non_editable_item(mime_type or "Unknown"))
            self.table.setItem(row, 2, self._non_editable_item(f"{size_mb:.2f}"))
            self.table.setItem(row, 3, self._non_editable_item(modified))

    def refresh_folder(self):
        if self.current_folder:
            self.import_folder(self.current_folder)
        else:
            QMessageBox.information(self, "No Folder", "Please import a folder first.")

    def select_all_files(self):
        """Sets all file checkboxes in the table to checked."""
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if isinstance(checkbox, QCheckBox):
                checkbox.setChecked(True)

    def unselect_all_files(self):
        """Sets all file checkboxes in the table to unchecked."""
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if isinstance(checkbox, QCheckBox):
                checkbox.setChecked(False)

    def _get_selected_files(self):
        """Helper to get a list of file paths for selected items."""
        selected_files = []
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if isinstance(checkbox, QCheckBox) and checkbox.isChecked():
                selected_files.append(checkbox.property("file_path"))
        return selected_files

    def _execute_rename_operation(self, operation_type, text_data):
        """
        Generic helper to perform rename operations (add/remove prefix/suffix).
        operation_type: 'add_prefix', 'add_suffix', 'remove_prefix', 'remove_suffix', 'add_both'
        text_data: string for single operations, dict {'prefix': s1, 'suffix': s2} for 'add_both'
        """
        selected_files = self._get_selected_files()

        if not selected_files:
            QMessageBox.warning(self, "No Selection", "Please select files to rename.")
            return

        text_to_use = ""
        if operation_type in ['add_prefix', 'add_suffix', 'remove_prefix', 'remove_suffix']:
            text_to_use = text_data
            if not text_to_use:
                QMessageBox.warning(self, "No Text Provided", f"Please enter text for the {operation_type.replace('_', ' ')} operation.")
                return
        elif operation_type == 'add_both':
            prefix = text_data.get('prefix', '')
            suffix = text_data.get('suffix', '')
            if not prefix and not suffix:
                QMessageBox.warning(self, "No Changes", "Please enter text for either prefix or suffix to add.")
                return
            
        operation_display_name = operation_type.replace('_', ' ').title().replace('Add_Both', 'Add Prefix/Suffix')
        confirm_msg = f"Are you sure you want to {operation_display_name.lower()}"
        if operation_type == 'add_both':
            confirm_msg += f" with prefix '{text_data.get('prefix', '')}' and suffix '{text_data.get('suffix', '')}' "
        else:
            confirm_msg += f" '{text_to_use}' "
        confirm_msg += f"for {len(selected_files)} file(s)?"

        confirm = QMessageBox.question(self, f"Confirm {operation_display_name}",
                                       confirm_msg,
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.No:
            return

        renamed_count = 0
        errors = []

        for original_path in selected_files:
            directory = os.path.dirname(original_path)
            old_filename_with_ext = os.path.basename(original_path)
            old_name, ext = os.path.splitext(old_filename_with_ext)
            
            new_name = old_name 

            if operation_type == 'add_prefix':
                new_name = f"{text_to_use}{old_name}"
            elif operation_type == 'add_suffix':
                new_name = f"{old_name}{text_to_use}"
            elif operation_type == 'remove_prefix':
                if old_name.startswith(text_to_use):
                    new_name = old_name[len(text_to_use):]
                else:
                    errors.append(f"Skipped '{old_filename_with_ext}': Does not start with '{text_to_use}'.")
                    continue
            elif operation_type == 'remove_suffix':
                if old_name.endswith(text_to_use):
                    new_name = old_name[:-len(text_to_use)]
                else:
                    errors.append(f"Skipped '{old_filename_with_ext}': Does not end with '{text_to_use}'.")
                    continue
            elif operation_type == 'add_both':
                prefix = text_data.get('prefix', '')
                suffix = text_data.get('suffix', '')
                new_name = f"{prefix}{old_name}{suffix}"


            new_filename_with_ext = f"{new_name}{ext}"
            new_path = os.path.join(directory, new_filename_with_ext)

            try:
                if original_path == new_path: 
                    errors.append(f"Skipped '{old_filename_with_ext}': New name is identical to old name.")
                    continue
                if os.path.exists(new_path): 
                    errors.append(f"Skipped '{old_filename_with_ext}': New file name '{new_filename_with_ext}' already exists.")
                    continue

                os.rename(original_path, new_path)
                renamed_count += 1
            except OSError as e:
                errors.append(f"Failed to rename '{old_filename_with_ext}': {e}")
            except Exception as e:
                errors.append(f"An unexpected error occurred with '{old_filename_with_ext}': {e}")

        self.refresh_folder()

        if renamed_count > 0:
            QMessageBox.information(self, f"{operation_display_name} Complete",
                                   f"Successfully {operation_display_name.lower()}d {renamed_count} file(s).")
        if errors:
            QMessageBox.warning(self, f"{operation_display_name} Errors",
                               f"Encountered errors for {len(errors)} file(s):\n" + "\n".join(errors))
        
        self.prefix_input.clear()
        self.suffix_input.clear()


    def perform_add_rename(self):
        """Handles adding prefix and/or suffix."""
        prefix = self.prefix_input.text()
        suffix = self.suffix_input.text()

        if not prefix and not suffix:
            QMessageBox.warning(self, "No Changes", "Please enter text for either prefix or suffix to add.")
            return
        
        if prefix and suffix:
            self._execute_rename_operation('add_both', {'prefix': prefix, 'suffix': suffix})
        elif prefix:
            self._execute_rename_operation('add_prefix', prefix)
        elif suffix:
            self._execute_rename_operation('add_suffix', suffix)


    def remove_prefix_from_files(self):
        """Handles removing a specified prefix."""
        text_to_remove = self.prefix_input.text()
        self._execute_rename_operation('remove_prefix', text_to_remove)

    def remove_suffix_from_files(self):
        """Handles removing a specified suffix."""
        text_to_remove = self.suffix_input.text()
        self._execute_rename_operation('remove_suffix', text_to_remove)

    def _non_editable_item(self, value):
        """Helper to create non-editable table items."""
        item = QTableWidgetItem(str(value))
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        return item
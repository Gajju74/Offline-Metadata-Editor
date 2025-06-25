from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFileDialog,
    QTableWidget, QTableWidgetItem, QLabel, QHeaderView, QHBoxLayout,
    QMessageBox, QCheckBox, QInputDialog, QProgressBar, QSlider
)
from PySide6.QtCore import Qt, QThread, Signal, QUrl, QTimer, QTime
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
import os
import mimetypes
from datetime import datetime
from audoai.noise_removal import NoiseRemovalClient

SUPPORTED_NOISE_FORMATS = (".wav", ".mp3", ".aac", ".flac", ".ogg", ".mp4", ".mov", ".avi", ".mkv", ".m4a")


class NoiseWorker(QThread):
    progress = Signal(int)
    finished = Signal(int)

    def __init__(self, files, client):
        super().__init__()
        self.files = files
        self.client = client

    def run(self):
        total = len(self.files)
        processed = 0
        for i, file_path in enumerate(self.files):
            try:
                result = self.client.process(file_path)
                output_path = os.path.splitext(file_path)[0] + "_cleaned" + os.path.splitext(file_path)[1]
                result.save(output_path)
                processed += 1
            except Exception as e:
                print(f"❌ Failed to clean {file_path}: {e}")
            self.progress.emit(int(((i + 1) / total) * 100))
        self.finished.emit(processed)


class NoiseCancellationBrowser(QWidget):
    current_folder = None

    def __init__(self, go_back_callback=None):  # ✅ accept go_back_callback
        super().__init__()
        self.go_back_callback = go_back_callback
        self.setMinimumSize(1600, 900)
        self.setWindowTitle("🧹 Noise Canceller – Select Files")

        self.api_key = None
        self.noise_removal_client = None
        self.selected_audio = None

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        self.setLayout(layout)

        # ✅ Combine all buttons into one top bar
        header_layout = QHBoxLayout()

        if self.go_back_callback:
            back_btn = QPushButton("← Back")
            back_btn.setFixedSize(100, 40)
            back_btn.clicked.connect(self.go_back_callback)
            header_layout.addWidget(back_btn)

        self.import_button = QPushButton("📁 Import Folder")
        self.import_button.setFixedHeight(40)
        self.import_button.clicked.connect(self.import_folder)

        self.api_button = QPushButton("🔐 Set API Key")
        self.api_button.setFixedHeight(40)
        self.api_button.clicked.connect(self.set_api_key)

        self.refresh_button = QPushButton("🔄 Refresh")
        self.refresh_button.setFixedHeight(40)
        self.refresh_button.clicked.connect(self.refresh_folder)

        self.play_button = QPushButton("▶️ Play")
        self.play_button.setFixedHeight(40)
        self.play_button.setEnabled(False)
        self.play_button.clicked.connect(self.play_audio)

        self.noise_button = QPushButton("🔊 Start Noise Cancellation")
        self.noise_button.setFixedHeight(40)
        self.noise_button.clicked.connect(self.process_selected_files)

        self.folder_label = QLabel("No folder selected")
        self.folder_label.setStyleSheet("font-weight: bold; font-size: 16px; padding-left: 15px;")

        header_layout.addWidget(self.import_button)
        header_layout.addWidget(self.api_button)
        header_layout.addWidget(self.refresh_button)
        header_layout.addWidget(self.play_button)
        header_layout.addWidget(self.noise_button)
        header_layout.addWidget(self.folder_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["File Name", "File Type", "Size (MB)", "Date Modified"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(self.handle_selection_change)
        layout.addWidget(self.table)

        self.media_player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.media_player.setAudioOutput(self.audio_output)

        self.player_bar = QHBoxLayout()
        self.play_toggle = QPushButton("⏸ Pause")
        self.play_toggle.setEnabled(False)
        self.play_toggle.setFixedHeight(30)
        self.play_toggle.clicked.connect(self.toggle_playback)
        self.player_bar.addWidget(self.play_toggle)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setEnabled(False)
        self.slider.sliderMoved.connect(lambda pos: self.media_player.setPosition(pos))
        self.player_bar.addWidget(self.slider)

        self.time_label = QLabel("00:00 / 00:00")
        self.player_bar.addWidget(self.time_label)
        layout.addLayout(self.player_bar)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_slider)

    def import_folder(self, folder=None):
        if not folder:
            folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if not folder:
            return
        self.current_folder = folder

        self.folder_label.setText(f"Imported: {folder}")
        self.table.setRowCount(0)

        for entry in os.listdir(folder):
            full_path = os.path.join(folder, entry)
            if not os.path.isfile(full_path):
                continue

            ext = os.path.splitext(entry)[1].lower()
            if ext not in SUPPORTED_NOISE_FORMATS:
                continue

            size_mb = os.path.getsize(full_path) / (1024 * 1024)
            modified = datetime.fromtimestamp(os.path.getmtime(full_path)).strftime("%Y-%m-%d %H:%M:%S")
            mime, _ = mimetypes.guess_type(full_path)

            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setRowHeight(row, 30)

            checkbox = QCheckBox(entry)
            checkbox.setProperty("file_path", full_path)
            self.table.setCellWidget(row, 0, checkbox)

            self.table.setItem(row, 1, self._non_editable_item(mime or ext))
            self.table.setItem(row, 2, self._non_editable_item(f"{size_mb:.2f}"))
            self.table.setItem(row, 3, self._non_editable_item(modified))

    def _non_editable_item(self, value):
        item = QTableWidgetItem(str(value))
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        return item

    def set_api_key(self):
        key, ok = QInputDialog.getText(self, "Set API Key", "Enter Audo AI API Key:")
        if ok and key:
            self.api_key = key
            try:
                self.noise_removal_client = NoiseRemovalClient(api_key=self.api_key)
                QMessageBox.information(self, "API Key Set", "API key saved successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to initialize client: {e}")

    def process_selected_files(self):
        if not self.noise_removal_client:
            QMessageBox.warning(self, "Missing API Key", "Please set an API key first.")
            return

        selected_files = []
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if isinstance(checkbox, QCheckBox) and checkbox.isChecked():
                selected_files.append(checkbox.property("file_path"))

        if not selected_files:
            QMessageBox.warning(self, "No Files", "No files were selected.")
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.worker = NoiseWorker(selected_files, self.noise_removal_client)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished.connect(self.handle_finished)
        self.worker.start()

    def refresh_folder(self):
        if self.current_folder:
            self.table.setRowCount(0)
            self.selected_audio = None
            self.play_button.setEnabled(False)
            self.play_toggle.setEnabled(False)
            self.slider.setEnabled(False)
            self.time_label.setText("00:00 / 00:00")
            self.import_folder(self.current_folder)

    def handle_finished(self, count):
        self.progress_bar.setVisible(False)
        QMessageBox.information(self, "Done", f"✅ Noise removed from {count} file(s).")

    def handle_selection_change(self):
        selected_indexes = self.table.selectedIndexes()
        if not selected_indexes:
            self.play_button.setEnabled(False)
            self.play_toggle.setEnabled(False)
            self.slider.setEnabled(False)
            return
        row = selected_indexes[0].row()
        file_checkbox = self.table.cellWidget(row, 0)
        if file_checkbox:
            file_path = file_checkbox.property("file_path")
            mime, _ = mimetypes.guess_type(file_path)
            if mime and mime.startswith("audio"):
                self.selected_audio = file_path
                self.play_button.setEnabled(True)
                self.play_toggle.setEnabled(True)
                self.slider.setEnabled(True)
                return
        self.play_button.setEnabled(False)
        self.play_toggle.setEnabled(False)
        self.slider.setEnabled(False)

    def play_audio(self):
        if hasattr(self, "selected_audio") and self.selected_audio:
            try:
                self.media_player.setSource(QUrl.fromLocalFile(self.selected_audio))
                self.media_player.play()
                self.play_toggle.setText("⏸ Pause")
                self.slider.setValue(0)
                self.timer.start(200)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to play audio: {e}")

    def toggle_playback(self):
        if self.media_player.playbackState() == QMediaPlayer.PlayingState:
            self.media_player.pause()
            self.play_toggle.setText("▶️ Play")
        else:
            self.media_player.play()
            self.play_toggle.setText("⏸ Pause")
            self.timer.start(200)

    def update_slider(self):
        if self.media_player.duration() > 0:
            pos = self.media_player.position()
            dur = self.media_player.duration()
            self.slider.setRange(0, dur)
            self.slider.setValue(pos)
            current_time = QTime(0, 0, 0).addMSecs(pos).toString("mm:ss")
            total_time = QTime(0, 0, 0).addMSecs(dur).toString("mm:ss")
            self.time_label.setText(f"{current_time} / {total_time}")
        else:
            self.slider.setValue(0)
            self.time_label.setText("00:00 / 00:00")
        if self.media_player.playbackState() != QMediaPlayer.PlayingState:
            self.timer.stop()

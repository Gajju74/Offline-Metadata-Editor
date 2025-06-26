from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QDialog, QSlider, QStyle, QHBoxLayout, QSizePolicy, QSpinBox, QCheckBox
from PySide6.QtCore import Qt, QUrl, QTime
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
import os
import mimetypes
from datetime import datetime

SUPPORTED_VIDEO_FORMATS = (".mp4", ".mov", ".avi", ".mkv")

class VideoEditorBrowser(QWidget):
    def __init__(self, go_back_callback=None):
        super().__init__()
        self.setWindowTitle("🎬 Video Editor Tool")
        self.setMinimumSize(1300, 900)
        self.go_back_callback = go_back_callback
        self.current_folder = None

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        self.setLayout(layout)

        header_layout = QHBoxLayout()

        if self.go_back_callback:
            back_button = QPushButton("← Back")
            back_button.setFixedSize(80, 35)
            back_button.clicked.connect(self.go_back_callback)
            header_layout.addWidget(back_button)

        self.import_button = QPushButton("📁 Import Folder")
        self.import_button.setFixedHeight(40)
        self.import_button.clicked.connect(lambda: self.import_folder())

        self.refresh_button = QPushButton("🔄 Refresh")
        self.refresh_button.setFixedHeight(40)
        self.refresh_button.clicked.connect(self.refresh_folder)

        self.mute_button = QPushButton("🔇 Mute Selected")
        self.mute_button.setFixedHeight(40)
        self.mute_button.clicked.connect(self.mute_selected_videos)

        self.folder_label = QLabel("No folder selected")
        self.folder_label.setStyleSheet("font-weight: bold; font-size: 16px; padding-left: 15px;")

        header_layout.addWidget(self.import_button)
        header_layout.addWidget(self.refresh_button)
        header_layout.addWidget(self.mute_button)
        header_layout.addWidget(self.folder_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["File Name", "Type", "Size (MB)", "Modified", "Edit"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def import_folder(self, folder=None):
        if folder is None:
            folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if not folder or not os.path.isdir(folder):
            return

        self.folder_label.setText(f"Imported: {folder}")
        self.table.setRowCount(0)
        self.current_folder = folder

        for entry in os.listdir(folder):
            full_path = os.path.join(folder, entry)
            if not os.path.isfile(full_path):
                continue

            ext = os.path.splitext(entry)[1].lower()
            if ext not in SUPPORTED_VIDEO_FORMATS:
                continue

            size_mb = os.path.getsize(full_path) / (1024 * 1024)
            modified = datetime.fromtimestamp(os.path.getmtime(full_path)).strftime("%Y-%m-%d %H:%M:%S")
            mime, _ = mimetypes.guess_type(full_path)

            row = self.table.rowCount()
            self.table.insertRow(row)

            checkbox = QCheckBox(entry)
            checkbox.setProperty("file_path", full_path)
            self.table.setCellWidget(row, 0, checkbox)
            self.table.setItem(row, 1, self._non_editable_item(mime or ext))
            self.table.setItem(row, 2, self._non_editable_item(f"{size_mb:.2f}"))
            self.table.setItem(row, 3, self._non_editable_item(modified))

            edit_button = QPushButton("Edit")
            edit_button.setProperty("file_path", full_path)
            edit_button.clicked.connect(self.handle_edit_click)
            self.table.setCellWidget(row, 4, edit_button)

    def handle_edit_click(self):
        sender = self.sender()
        file_path = sender.property("file_path")
        self.open_video_player(file_path)

    def open_video_player(self, file_path):
        dialog = QDialog(self)
        dialog.setWindowTitle("🎞 Video Preview & Trim")
        dialog.setMinimumSize(960, 600)
        layout = QVBoxLayout(dialog)

        video_widget = QVideoWidget()
        layout.addWidget(video_widget)

        player = QMediaPlayer()
        audio_output = QAudioOutput()
        player.setAudioOutput(audio_output)
        player.setVideoOutput(video_widget)
        player.setSource(QUrl.fromLocalFile(file_path))

        control_layout = QHBoxLayout()

        play_button = QPushButton()
        play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        def toggle_play():
            if player.playbackState() == QMediaPlayer.PlayingState:
                player.pause()
                play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            else:
                player.play()
                play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        play_button.clicked.connect(toggle_play)
        control_layout.addWidget(play_button)

        time_label = QLabel("00:00")
        control_layout.addWidget(time_label)

        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 0)
        slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        control_layout.addWidget(slider)

        total_time_label = QLabel("00:00")
        control_layout.addWidget(total_time_label)

        volume_slider = QSlider(Qt.Horizontal)
        volume_slider.setRange(0, 100)
        volume_slider.setValue(audio_output.volume() * 100)
        volume_slider.setFixedWidth(100)
        volume_slider.valueChanged.connect(lambda val: audio_output.setVolume(val / 100))
        control_layout.addWidget(volume_slider)

        layout.addLayout(control_layout)

        trim_layout = QHBoxLayout()
        trim_layout.addWidget(QLabel("Start (sec):"))
        start_spin = QSpinBox()
        start_spin.setRange(0, 0)
        trim_layout.addWidget(start_spin)

        trim_layout.addWidget(QLabel("End (sec):"))
        end_spin = QSpinBox()
        end_spin.setRange(0, 0)
        trim_layout.addWidget(end_spin)

        trim_button = QPushButton("✂ Trim Video")
        def trim_video():
            start = start_spin.value()
            end = end_spin.value()
            if end <= start:
                QMessageBox.warning(dialog, "Invalid Range", "End time must be greater than start time.")
                return
            output_file = os.path.splitext(file_path)[0] + f"_trimmed_{start}_{end}.mp4"
            cmd = f"ffmpeg -y -i \"{file_path}\" -ss {start} -to {end} -c copy \"{output_file}\""
            os.system(cmd)
            QMessageBox.information(dialog, "Trim Complete", f"Saved to: {output_file}")
        trim_button.clicked.connect(trim_video)
        trim_layout.addWidget(trim_button)
        layout.addLayout(trim_layout)

        def update_duration(duration):
            slider.setRange(0, duration)
            total_time_label.setText(QTime(0, 0, 0).addMSecs(duration).toString("mm:ss"))
            start_spin.setMaximum(duration // 1000)
            end_spin.setMaximum(duration // 1000)
            end_spin.setValue(duration // 1000)

        def update_position(position):
            slider.blockSignals(True)
            slider.setValue(position)
            slider.blockSignals(False)
            time_label.setText(QTime(0, 0, 0).addMSecs(position).toString("mm:ss"))

        def seek(position):
            player.setPosition(position)

        player.durationChanged.connect(update_duration)
        player.positionChanged.connect(update_position)
        slider.sliderMoved.connect(seek)

        player.play()
        dialog.exec()

    def _non_editable_item(self, value):
        item = QTableWidgetItem(str(value))
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        return item

    def refresh_folder(self):
        if self.current_folder and os.path.isdir(self.current_folder):
            self.import_folder(self.current_folder)

    def mute_selected_videos(self):
        muted = 0
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if not isinstance(checkbox, QCheckBox) or not checkbox.isChecked():
                continue

            file_path = checkbox.property("file_path")
            output_path = os.path.splitext(file_path)[0] + "_muted.mp4"
            cmd = f"ffmpeg -y -i \"{file_path}\" -an \"{output_path}\""
            os.system(cmd)
            muted += 1

        if muted:
            QMessageBox.information(self, "Muted", f"Muted {muted} video(s) successfully.")
        else:
            QMessageBox.information(self, "No Selection", "No videos were selected for muting.")
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QDialog, QSlider, QStyle, QSizePolicy, QSpinBox, QCheckBox, QGraphicsScene, QGraphicsView, QGraphicsPixmapItem, QProgressDialog
from PySide6.QtCore import Qt, QUrl, QTime, QRect, QPoint, QSize, QThread, Signal
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtGui import QPixmap, QMouseEvent, QPen, QColor
import os
import mimetypes
from datetime import datetime
import tempfile
import subprocess
import re # Added for parsing FFmpeg output

SUPPORTED_VIDEO_FORMATS = (".mp4", ".mov", ".avi", ".mkv")

class ScreenshotSelectionWidget(QGraphicsView):
    def __init__(self, pixmap):
        super().__init__()
        self.setScene(QGraphicsScene(self))
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene().addItem(self.pixmap_item)
        self.origin = QPoint()
        self.selection_rects = []
        self.rect_items = []
        self.temp_rect = None

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.origin = self.mapToScene(event.pos()).toPoint()
            self.temp_rect = self.scene().addRect(QRect(self.origin, QSize()), QPen(QColor(0, 120, 215), 2))
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.temp_rect:
            current_pos = self.mapToScene(event.pos()).toPoint()
            rect = QRect(self.origin, current_pos).normalized()
            self.temp_rect.setRect(rect)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton and self.temp_rect:
            rect = self.temp_rect.rect().toRect()
            self.selection_rects.append(rect)
            self.rect_items.append(self.temp_rect)  # Store the rectangle item
            print(f"Selected Region: x={rect.x()}, y={rect.y()}, w={rect.width()}, h={rect.height()}")
            self.temp_rect = None
        super().mouseReleaseEvent(event)
    
    def remove_last_rectangle(self):
        """Remove the last drawn rectangle from the scene"""
        if self.rect_items:
            last_rect = self.rect_items.pop()
            self.scene().removeItem(last_rect)
            if self.selection_rects:
                self.selection_rects.pop()
            self.viewport().update()  # Refresh the view

class BlurWorker(QThread):
    progress_updated = Signal(int) # Emits percentage (0-100)
    blur_done = Signal(bool, str) # Emits (success: bool, message: str)

    def __init__(self, file_path, filter_chain, output_path, total_duration_ms):
        super().__init__()
        self.file_path = file_path
        self.filter_chain = filter_chain
        self.output_path = output_path
        self.total_duration_ms = total_duration_ms
        self.is_cancelled = False

    def run(self):
        cmd = (f'ffmpeg -y -i "{self.file_path}" '
                f'-filter_complex "{self.filter_chain}" '
                f'-map "[out_v]" -c:a copy "{self.output_path}"')

        process = None
        try:
            process = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, universal_newlines=True)

            total_seconds = self.total_duration_ms / 1000
            for line in process.stderr:
                if self.is_cancelled:
                    process.terminate()
                    self.blur_done.emit(False, "Blurring cancelled.")
                    return

                if "time=" in line and "total_time=" not in line:
                    match = re.search(r"time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})", line)
                    if match:
                        h, m, s, ms_hundredths = map(int, match.groups())
                        current_seconds = h * 3600 + m * 60 + s + ms_hundredths / 100
                        
                        if total_seconds > 0:
                            progress_percent = int((current_seconds / total_seconds) * 100)
                            progress_percent = max(0, min(100, progress_percent)) # Clamp to 0-100
                            self.progress_updated.emit(progress_percent)

            process.wait()
            
            if process.returncode == 0:
                self.blur_done.emit(True, f"Blurred video saved to:\n{self.output_path}")
            else:
                self.blur_done.emit(False, f"FFmpeg process failed with error code {process.returncode}. Check console for details.")

        except Exception as e:
            if process:
                process.terminate()
            self.blur_done.emit(False, f"An unexpected error occurred during blur: {e}")

    def cancel(self):
        """Allows cancelling the FFmpeg process."""
        self.is_cancelled = True

class VideoEditorBrowser(QWidget):
    def __init__(self, go_back_callback=None):
        super().__init__()
        self.setWindowTitle("Video Editor Tool")
        self.setMinimumSize(1300, 900)
        self.go_back_callback = go_back_callback
        self.current_folder = None
        self.blur_worker = None # Keep a reference to the worker

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
        self.import_button.clicked.connect(self.import_folder)

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

    def import_folder(self):
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
        dialog.setWindowTitle("Video Preview & Trim")
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
        volume_slider.setValue(int(audio_output.volume() * 100)) # Ensure integer value
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
            end_spin.setValue(duration // 1000) # Set end time to max duration by default

        def update_position(position):
            # Only update slider if not currently dragging it
            if not slider.isSliderDown():
                slider.blockSignals(True)
                slider.setValue(position)
                slider.blockSignals(False)
            time_label.setText(QTime(0, 0, 0).addMSecs(position).toString("mm:ss"))

        def seek(position):
            player.setPosition(position)

        player.durationChanged.connect(update_duration)
        player.positionChanged.connect(update_position)
        slider.sliderMoved.connect(seek)

        blur_button = QPushButton("Blur Region")
        blur_button.setFixedSize(140, 35)
        blur_button.setStyleSheet("background-color: #444; color: white; font-weight: bold; border-radius: 6px;")
        layout.addWidget(blur_button)

        def show_screenshot():
            position_ms = player.position()
            video_duration_ms = player.duration() # Get total video duration for progress calculation

            # Capture a temporary screenshot
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                tmp_path = tmp.name
            # Ensure the screenshot command uses correct time format for ffmpeg and correct input path quoting
            cmd = f"ffmpeg -y -ss {position_ms/1000:.2f} -i \"{file_path}\" -frames:v 1 \"{tmp_path}\""
            # Use subprocess.run for simple blocking calls like this, check=True for error
            try:
                subprocess.run(cmd, shell=True, check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                QMessageBox.warning(dialog, "Error", f"Failed to capture screenshot: {e.stderr.decode()}")
                return

            screenshot_dialog = QDialog(dialog)
            screenshot_dialog.setWindowTitle("Frame Screenshot")
            screenshot_layout = QVBoxLayout(screenshot_dialog)

            pixmap = QPixmap(tmp_path)
            if pixmap.isNull():
                QMessageBox.warning(dialog, "Error", "Failed to load captured screenshot")
                os.unlink(tmp_path)
                return

            view = ScreenshotSelectionWidget(pixmap)
            screenshot_layout.addWidget(view)

            # Create button layout for undo and finish
            button_layout = QHBoxLayout()
            
            undo_button = QPushButton("↩ Undo Last")
            undo_button.setFixedSize(120, 35)
            undo_button.setStyleSheet("background-color: #666; color: white; font-weight: bold; border-radius: 6px;")
            undo_button.clicked.connect(view.remove_last_rectangle)
            button_layout.addWidget(undo_button)
            
            finish_blur_button = QPushButton("✅ Finish Blurring")
            finish_blur_button.setFixedSize(140, 35)
            finish_blur_button.setStyleSheet("background-color: #2E7D32; color: white; font-weight: bold; border-radius: 6px;")
            button_layout.addWidget(finish_blur_button)
            
            screenshot_layout.addLayout(button_layout)

            def perform_blur():
                if not view.selection_rects:
                    QMessageBox.warning(screenshot_dialog, "No Selection", 
                                        "Please select at least one region to blur.")
                    return

                # Build filter_complex string for multiple regions
                filter_chain = ""
                base = "[0:v]"   # Start with the original video as base
                
                # Create all blurred regions first
                for i, rect in enumerate(view.selection_rects):
                    x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
                    filter_chain += f"[0:v]crop={w}:{h}:{x}:{y},boxblur=10[blur{i}];"
                
                # Then overlay them sequentially
                current = base
                for i, rect in enumerate(view.selection_rects):
                    x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
                    filter_chain += f"{current}[blur{i}]overlay={x}:{y}[ovl{i}];"
                    current = f"[ovl{i}]"
                
                # Add a final split to name the output stream for '-map'
                filter_chain += f"{current}split[out_v];" 

                output_path = os.path.splitext(file_path)[0] + "_blurred.mp4"
                
                # --- Progress Dialog and Worker Setup ---
                blur_progress_dialog = QProgressDialog("Applying blur...", "Cancel", 0, 100, screenshot_dialog)
                blur_progress_dialog.setWindowModality(Qt.WindowModal)
                blur_progress_dialog.setMinimumDuration(0)
                blur_progress_dialog.setMinimumWidth(400) # Set a readable width
                blur_progress_dialog.setValue(0)
                blur_progress_dialog.setWindowTitle("Blurring Progress")

                # Pause player during blurring to avoid conflicts and save resources
                player.pause()

                # Instantiate the worker thread, using self.blur_worker to keep a strong reference
                self.blur_worker = BlurWorker(file_path, filter_chain, output_path, video_duration_ms)

                # Connect worker signals to dialog updates and completion handling
                self.blur_worker.progress_updated.connect(blur_progress_dialog.setValue)
                
                # Use a lambda to pass additional arguments to on_blur_done
                self.blur_worker.blur_done.connect(
                    lambda success, msg: on_blur_done(success, msg, blur_progress_dialog, self.blur_worker)
                )
                
                # Connect cancel button to worker's cancel method
                blur_progress_dialog.canceled.connect(self.blur_worker.cancel) 

                self.blur_worker.start() # Start the blurring process in the background

            def on_blur_done(success, message, progress_dialog_instance, worker_instance):
                """Handle the completion of the blur worker."""
                progress_dialog_instance.close()
                if success:
                    QMessageBox.information(screenshot_dialog, "Success", message)
                    screenshot_dialog.accept() # Close the screenshot dialog on successful blur
                else:
                    QMessageBox.critical(screenshot_dialog, "Error", f"Blur failed: {message}")
                player.play() # Resume player after blur is done/failed
                worker_instance.deleteLater() # Clean up the worker thread

            finish_blur_button.clicked.connect(perform_blur)
            screenshot_dialog.resize(pixmap.width() + 20, pixmap.height() + 150)
            screenshot_dialog.exec()
            
            # Clean up temporary screenshot
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

        blur_button.clicked.connect(show_screenshot)
        layout.addWidget(blur_button)

        player.play()
        dialog.exec()

    def _non_editable_item(self, value):
        item = QTableWidgetItem(str(value))
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        return item

    def refresh_folder(self):
        if self.current_folder and os.path.isdir(self.current_folder):
            self.folder_label.setText(f"Imported: {self.current_folder}")
            self.table.setRowCount(0)

            for entry in os.listdir(self.current_folder):
                full_path = os.path.join(self.current_folder, entry)
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
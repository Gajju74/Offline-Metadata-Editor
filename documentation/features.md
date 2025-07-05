# 🧰 Offline File Metadata Editor & Converter – Feature Checklist

## ✅ Core Functionalities

### 🧾 File Selection & Management
- [ ] Multi-file selector (drag-and-drop or file picker)
- [ ] Show file list with name, type, size, and basic metadata
- [ ] Option to remove selected files from the list
- [ ] File filtering by type (image, video)

### 🏷️ Metadata Viewing & Editing

#### 📷 For Images (JPEG, PNG, HEIC)
- [ ] View EXIF metadata (date taken, camera model, orientation, etc.)
- [ ] Edit specific fields (e.g., date taken, GPS, device model)
- [ ] Save updated metadata to original or new file

#### 🎞️ For Videos (MP4, AVI, MOV)
- [ ] View metadata (duration, codec, frame rate, title, date)
- [ ] Edit metadata using `ffmpeg` (e.g., title, creation date)
- [ ] Save updated metadata

### 🔁 Metadata Operations
- [ ] Copy metadata from one file to multiple files
- [ ] Erase metadata (clear specific fields or all)
- [ ] Apply metadata templates (device-based presets like iPhone)
- [ ] Randomize metadata:
  - [ ] Specify date range (e.g., Jan 1 to Mar 30, 2025)
  - [ ] Apply random dates to selected files

---

## 🔄 Conversion & Video Operations

### 🖼️ Image Format Conversion
- [ ] Convert between `.heic`, `.jpg`, `.png`, etc.
- [ ] Option to retain or strip metadata during conversion

### 🎥 Video Format Conversion
- [ ] Convert between `.mp4`, `.avi`, `.mov`, etc.
- [ ] Retain or modify metadata during conversion 

### 🔇 Video Editing Utilities
- [ ] Mute audio (remove audio track)
- [ ] Change frame rate (e.g., from 60fps to 30fps)

---

## ⚙️ Batch & Template Features

### 📦 Batch Processing
- [ ] Select multiple files for bulk operations
- [ ] Apply any of the above tasks to a batch
- [ ] Show progress indicator for each file

### 🧰 Metadata Templates
- [ ] Save template with fields like:
  - Device model
  - Date/time
  - Custom text fields
- [ ] Apply template to one or more files
- [ ] Manage templates (Add, Edit, Delete)
- [ ] Store templates in SQLite locally

---

## 🧑‍💻 User Interface & UX

### 🖥️ UI Components
- [ ] Dashboard: file list + file preview
- [ ] Form-based metadata editor (with input types like date picker, dropdown)
- [ ] Template manager section
- [ ] Settings page (default export paths, metadata handling rules)

### 🔔 Feedback & Notifications
- [ ] Status bar showing operation in progress
- [ ] Error/success toast notifications
- [ ] Optional logging console (for debugging or admin use)

---

## 📁 File Handling & System Features

### 📁 File Operations
- [ ] Choose output directory
- [ ] Save as new copy or overwrite
- [ ] File renaming options (e.g., based on metadata)

### 🔐 Offline & Security
- [ ] 100% offline processing
- [ ] No data sent externally
- [ ] Clear permission handling for reading/writing files

---

## 🧩 Optional (Advanced/Future Features)
- [ ] Image preview
- [ ] Thumbnail generation
- [ ] Timeline view (e.g., image gallery by date)
- [ ] File comparison view (before vs after metadata)

# Portable-Notes
A lightweight, portable markdown note-taking application built in Python with Tkinter. Fast, simple, and 100% offline — all notes saved as plain text Markdown files. Easy to backup, move, and run on any modern Windows system. It is a minimalist, portable markdown note-taking app built with Python and Tkinter. It focuses on critical features like markdown editing, note linking, tags, search, and easy backup. No cloud required — your notes are always local and under your control.

## Features

- **Markdown support** with live preview
- **Folder organization** for notes
- **Tags and full-text search**
- **Note linking** (Obsidian-style `[[links]]`)
- **Backlinks** panel
- **To-do checkboxes**
- **Light/dark themes**
- **Quick note creation and templates**
- **Distraction-free writing interface**
- **100% offline, no cloud dependency**
- **Easy backup:** just copy the `notes` folder
- **Portable:** works from USB or cloud drive

## Getting Started

### Prerequisites

- Python 3.8 or later (Tkinter included)
- Windows 11+

### Install and Run

1. **Clone the repository:**
    ```
    git clone https://github.com/<your-username>/lightweight-notes.git
    cd lightweight-notes
    ```

2. **Run the app:**
    ```
    python mynotes.py
    ```

3. **Build standalone executable (optional):**
    ```
    python -m pip install pyinstaller
    python -m PyInstaller --onefile --windowed --name="MyNotes" mynotes.py
    ```
    Find `MyNotes.exe` in the `dist` folder.

### Usage

- All notes are stored in the `notes/` directory as `.md` files.
- Use the app to create, edit, search, and organize your notes.
- To back up, simply copy the `notes/` folder anywhere.
- To move your notes, just transfer the folder and run the app.

## License

Distributed under the MIT License. See `LICENSE` for details.


## Contributing

Pull requests and feature suggestions are welcome. Please open an issue to discuss changes or improvements.

## Inspiration

Inspired by Obsidian, OneNote, and other leading note-taking applications, but keeping only the core features for speed and simplicity.

---


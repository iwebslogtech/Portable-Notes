# Portable Notes Web

A private, local-first Markdown knowledge base inspired by Obsidian, Notepad++, and OneNote. It runs in your browser on `localhost`, requires no cloud account, and stores everything in a local SQLite database.

## Highlights

- Markdown editor with live Reader and split view
- Obsidian-style `[[wiki links]]`, outgoing links, and backlinks
- Fast full-text search across titles, content, folders, and tags
- Folders, tags, favorites, pinned notes, trash, and autosave
- Light/dark themes and keyboard shortcuts
- ZIP export containing Markdown files plus a JSON backup
- Responsive interface and 100% local storage
- No third-party Python packages required

## Run

```bash
git clone https://github.com/YOUR-USERNAME/portable-notes-web.git
cd portable-notes-web
python app.py
```

The app opens at <http://127.0.0.1:8765>. Press `Ctrl+C` in the terminal to stop it.

### Windows shortcut

Double-click `start.bat`.

## Keyboard shortcuts

- `Ctrl+N`: New note
- `Ctrl+S`: Save now
- `Ctrl+K`: Focus search
- `Ctrl+Shift+P`: Cycle editor, split, and reader modes

## Data and privacy

Notes are stored in `data/notes.db`. The server binds only to `127.0.0.1`, so it is not exposed to other devices. Use Export regularly for portable Markdown backups. Do not commit the `data/` directory.

## Project structure

```text
portable-notes-web/
├── app.py
├── static/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── data/
├── start.bat
├── start.sh
├── LICENSE
├── CONTRIBUTING.md
├── SECURITY.md
├── CHANGELOG.md
└── .github/
```

## Roadmap

See [ROADMAP.md](ROADMAP.md). Suggested next milestones include note attachments, nested folders, database encryption, graph view, and optional sync adapters.

## License

MIT. See [LICENSE](LICENSE).

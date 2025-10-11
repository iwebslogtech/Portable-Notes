"""
MyNotes - Lightweight Markdown Note-Taking Application
A simple, portable note-taking app with markdown support
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from tkinter.scrolledtext import ScrolledText
import os
import json
import re
from datetime import datetime
from pathlib import Path

class MyNotesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MyNotes - Lightweight Note Taking")
        self.root.geometry("1200x700")
        
        # Application settings
        self.notes_dir = Path("notes")
        self.notes_dir.mkdir(exist_ok=True)
        self.metadata_file = Path("metadata.json")
        self.current_file = None
        self.current_theme = "light"
        self.unsaved_changes = False
        
        # Load metadata
        self.load_metadata()
        
        # Setup UI
        self.setup_menu()
        self.setup_ui()
        self.setup_keyboard_shortcuts()
        self.apply_theme()
        
        # Load last opened note or create new
        self.refresh_notes_list()
        
    def setup_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Note (Ctrl+N)", command=self.new_note)
        file_menu.add_command(label="Save (Ctrl+S)", command=self.save_note)
        file_menu.add_command(label="Delete Note", command=self.delete_note)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.exit_app)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Find (Ctrl+F)", command=self.find_text)
        edit_menu.add_command(label="Insert Link [[]]", command=self.insert_link)
        edit_menu.add_command(label="Insert Checkbox", command=self.insert_checkbox)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Toggle Theme", command=self.toggle_theme)
        view_menu.add_command(label="Refresh List", command=self.refresh_notes_list)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Markdown Guide", command=self.show_markdown_guide)
        help_menu.add_command(label="About", command=self.show_about)
        
    def setup_ui(self):
        """Setup main user interface"""
        # Main container with three panes
        main_container = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=3)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Left sidebar - Notes list
        self.setup_sidebar(main_container)
        
        # Middle - Editor
        self.setup_editor(main_container)
        
        # Right sidebar - Preview/Backlinks
        self.setup_preview(main_container)
        
    def setup_sidebar(self, parent):
        """Setup left sidebar with notes list"""
        sidebar = tk.Frame(parent, width=250)
        
        # Search box
        search_frame = tk.Frame(sidebar)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(search_frame, text="🔍 Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.filter_notes())
        search_entry = tk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Notes list
        list_frame = tk.Frame(sidebar)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        tk.Label(list_frame, text="Notes", font=("Arial", 10, "bold")).pack()
        
        # Listbox with scrollbar
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.notes_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.notes_listbox.pack(fill=tk.BOTH, expand=True)
        self.notes_listbox.bind('<<ListboxSelect>>', self.on_note_select)
        scrollbar.config(command=self.notes_listbox.yview)
        
        # Tags section
        tags_frame = tk.Frame(sidebar)
        tags_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(tags_frame, text="Tags:", font=("Arial", 9)).pack(anchor=tk.W)
        self.tags_entry = tk.Entry(tags_frame)
        self.tags_entry.pack(fill=tk.X)
        self.tags_entry.bind('<Return>', lambda e: self.update_tags())
        
        tk.Button(tags_frame, text="Update Tags", command=self.update_tags).pack(pady=2)
        
        parent.add(sidebar)
        
    def setup_editor(self, parent):
        """Setup middle editor pane"""
        editor_frame = tk.Frame(parent)
        
        # Title entry
        title_frame = tk.Frame(editor_frame)
        title_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(title_frame, text="Title:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.title_var = tk.StringVar()
        self.title_var.trace('w', lambda *args: self.mark_unsaved())
        self.title_entry = tk.Entry(title_frame, textvariable=self.title_var, font=("Arial", 12))
        self.title_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Status bar
        status_frame = tk.Frame(editor_frame)
        status_frame.pack(fill=tk.X, padx=5)
        
        self.status_label = tk.Label(status_frame, text="Ready", anchor=tk.W, fg="gray")
        self.status_label.pack(side=tk.LEFT)
        
        self.word_count_label = tk.Label(status_frame, text="Words: 0", anchor=tk.E, fg="gray")
        self.word_count_label.pack(side=tk.RIGHT)
        
        # Text editor
        self.text_editor = ScrolledText(editor_frame, wrap=tk.WORD, undo=True, 
                                        font=("Consolas", 11), padx=10, pady=10)
        self.text_editor.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.text_editor.bind('<KeyRelease>', self.on_text_change)
        self.text_editor.bind('[[', self.on_link_start)
        
        parent.add(editor_frame)
        
    def setup_preview(self, parent):
        """Setup right preview/backlinks pane"""
        preview_frame = tk.Frame(parent, width=300)
        
        # Tabs for Preview and Backlinks
        notebook = ttk.Notebook(preview_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Preview tab
        preview_tab = tk.Frame(notebook)
        notebook.add(preview_tab, text="Preview")
        
        self.preview_text = ScrolledText(preview_tab, wrap=tk.WORD, state=tk.DISABLED,
                                         font=("Arial", 10), padx=10, pady=10)
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        
        # Backlinks tab
        backlinks_tab = tk.Frame(notebook)
        notebook.add(backlinks_tab, text="Backlinks")
        
        tk.Label(backlinks_tab, text="Notes linking here:", font=("Arial", 9, "bold")).pack(pady=5)
        self.backlinks_listbox = tk.Listbox(backlinks_tab)
        self.backlinks_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.backlinks_listbox.bind('<Double-Button-1>', self.open_backlink)
        
        parent.add(preview_frame)
        
    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts"""
        self.root.bind('<Control-n>', lambda e: self.new_note())
        self.root.bind('<Control-s>', lambda e: self.save_note())
        self.root.bind('<Control-f>', lambda e: self.find_text())
        self.root.bind('<Control-q>', lambda e: self.exit_app())
        
    # Core functionality methods
    
    def new_note(self):
        """Create a new note"""
        if self.unsaved_changes:
            if not messagebox.askyesno("Unsaved Changes", "Save current note?"):
                self.unsaved_changes = False
            else:
                self.save_note()
        
        title = simpledialog.askstring("New Note", "Enter note title:")
        if not title:
            return
            
        # Create safe filename
        filename = self.sanitize_filename(title) + ".md"
        filepath = self.notes_dir / filename
        
        # Check if exists
        if filepath.exists():
            messagebox.showwarning("Exists", "Note with this title already exists!")
            return
            
        self.current_file = filepath
        self.title_var.set(title)
        self.text_editor.delete(1.0, tk.END)
        self.tags_entry.delete(0, tk.END)
        self.unsaved_changes = False
        
        self.refresh_notes_list()
        self.update_status(f"Created: {title}")
        
    def save_note(self):
        """Save current note"""
        if not self.current_file:
            self.new_note()
            return
            
        title = self.title_var.get().strip()
        if not title:
            messagebox.showwarning("No Title", "Please enter a note title!")
            return
            
        content = self.text_editor.get(1.0, tk.END).strip()
        
        # Save to file
        try:
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(f"# {title}\n\n{content}")
            
            # Update metadata
            tags = [t.strip() for t in self.tags_entry.get().split(',') if t.strip()]
            self.update_metadata(self.current_file.name, title, tags)
            
            self.unsaved_changes = False
            self.update_status(f"Saved: {title}")
            self.refresh_notes_list()
            self.update_backlinks()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {str(e)}")
            
    def delete_note(self):
        """Delete current note"""
        if not self.current_file:
            return
            
        if messagebox.askyesno("Delete", "Delete this note permanently?"):
            try:
                self.current_file.unlink()
                
                # Remove from metadata
                if self.current_file.name in self.metadata:
                    del self.metadata[self.current_file.name]
                    self.save_metadata()
                
                self.current_file = None
                self.title_var.set("")
                self.text_editor.delete(1.0, tk.END)
                self.tags_entry.delete(0, tk.END)
                
                self.refresh_notes_list()
                self.update_status("Note deleted")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete: {str(e)}")
                
    def on_note_select(self, event):
        """Handle note selection from list"""
        if not self.notes_listbox.curselection():
            return
            
        if self.unsaved_changes:
            if messagebox.askyesno("Unsaved Changes", "Save current note?"):
                self.save_note()
            self.unsaved_changes = False
            
        index = self.notes_listbox.curselection()[0]
        filename = self.notes_listbox.get(index)
        
        # Extract actual filename from display text
        match = re.search(r'\((.+?\.md)\)', filename)
        if match:
            filename = match.group(1)
        else:
            filename = self.sanitize_filename(filename.split('[')[0].strip()) + ".md"
        
        self.load_note(filename)
        
    def load_note(self, filename):
        """Load a note from file"""
        filepath = self.notes_dir / filename
        if not filepath.exists():
            return
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract title and content
            lines = content.split('\n')
            title = lines[0].replace('#', '').strip() if lines else filename.replace('.md', '')
            note_content = '\n'.join(lines[2:]) if len(lines) > 2 else '\n'.join(lines[1:])
            
            self.current_file = filepath
            self.title_var.set(title)
            self.text_editor.delete(1.0, tk.END)
            self.text_editor.insert(1.0, note_content)
            
            # Load tags
            meta = self.metadata.get(filename, {})
            tags = meta.get('tags', [])
            self.tags_entry.delete(0, tk.END)
            self.tags_entry.insert(0, ', '.join(tags))
            
            self.unsaved_changes = False
            self.update_status(f"Loaded: {title}")
            self.update_preview()
            self.update_backlinks()
            self.update_word_count()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load note: {str(e)}")
            
    def refresh_notes_list(self):
        """Refresh the notes list"""
        self.notes_listbox.delete(0, tk.END)
        
        search_term = self.search_var.get().lower()
        
        # Get all markdown files
        notes = sorted(self.notes_dir.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True)
        
        for note_file in notes:
            meta = self.metadata.get(note_file.name, {})
            title = meta.get('title', note_file.stem)
            tags = meta.get('tags', [])
            
            # Filter by search term
            if search_term:
                if search_term not in title.lower() and not any(search_term in tag.lower() for tag in tags):
                    continue
            
            # Display format: Title [tags] (filename)
            display_text = f"{title}"
            if tags:
                display_text += f" [{', '.join(tags[:2])}]"
            
            self.notes_listbox.insert(tk.END, display_text)
            
    def filter_notes(self):
        """Filter notes based on search"""
        self.refresh_notes_list()
        
    def update_preview(self):
        """Update markdown preview"""
        content = self.text_editor.get(1.0, tk.END)
        
        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete(1.0, tk.END)
        
        # Simple markdown rendering
        lines = content.split('\n')
        for line in lines:
            # Headers
            if line.startswith('# '):
                self.preview_text.insert(tk.END, line[2:] + '\n', 'h1')
            elif line.startswith('## '):
                self.preview_text.insert(tk.END, line[3:] + '\n', 'h2')
            elif line.startswith('### '):
                self.preview_text.insert(tk.END, line[4:] + '\n', 'h3')
            # Bold
            elif '**' in line:
                parts = re.split(r'\*\*(.+?)\*\*', line)
                for i, part in enumerate(parts):
                    if i % 2 == 1:
                        self.preview_text.insert(tk.END, part, 'bold')
                    else:
                        self.preview_text.insert(tk.END, part)
                self.preview_text.insert(tk.END, '\n')
            # Links
            elif '[[' in line:
                parts = re.split(r'\[\[(.+?)\]\]', line)
                for i, part in enumerate(parts):
                    if i % 2 == 1:
                        self.preview_text.insert(tk.END, part, 'link')
                    else:
                        self.preview_text.insert(tk.END, part)
                self.preview_text.insert(tk.END, '\n')
            else:
                self.preview_text.insert(tk.END, line + '\n')
        
        # Configure tags for styling
        self.preview_text.tag_config('h1', font=("Arial", 16, "bold"))
        self.preview_text.tag_config('h2', font=("Arial", 14, "bold"))
        self.preview_text.tag_config('h3', font=("Arial", 12, "bold"))
        self.preview_text.tag_config('bold', font=("Arial", 10, "bold"))
        self.preview_text.tag_config('link', foreground="blue", underline=True)
        
        self.preview_text.config(state=tk.DISABLED)
        
    def update_backlinks(self):
        """Find and display notes that link to current note"""
        self.backlinks_listbox.delete(0, tk.END)
        
        if not self.current_file:
            return
            
        current_title = self.title_var.get()
        
        # Search all notes for links to current note
        for note_file in self.notes_dir.glob("*.md"):
            if note_file == self.current_file:
                continue
                
            try:
                with open(note_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Find [[links]]
                if f"[[{current_title}]]" in content:
                    meta = self.metadata.get(note_file.name, {})
                    title = meta.get('title', note_file.stem)
                    self.backlinks_listbox.insert(tk.END, title)
                    
            except Exception:
                pass
                
    def open_backlink(self, event):
        """Open note from backlinks"""
        if not self.backlinks_listbox.curselection():
            return
            
        title = self.backlinks_listbox.get(self.backlinks_listbox.curselection()[0])
        
        # Find file by title
        for filename, meta in self.metadata.items():
            if meta.get('title') == title:
                self.load_note(filename)
                break
                
    def find_text(self):
        """Find text in current note"""
        search = simpledialog.askstring("Find", "Enter text to find:")
        if not search:
            return
            
        # Remove previous highlights
        self.text_editor.tag_remove('found', 1.0, tk.END)
        
        # Search and highlight
        start = 1.0
        while True:
            pos = self.text_editor.search(search, start, tk.END, nocase=True)
            if not pos:
                break
            end = f"{pos}+{len(search)}c"
            self.text_editor.tag_add('found', pos, end)
            start = end
            
        self.text_editor.tag_config('found', background='yellow')
        
        # Focus first match
        first_match = self.text_editor.search(search, 1.0, tk.END, nocase=True)
        if first_match:
            self.text_editor.see(first_match)
            
    def insert_link(self):
        """Insert wiki-style link"""
        self.text_editor.insert(tk.INSERT, "[[]]")
        # Move cursor inside brackets
        self.text_editor.mark_set(tk.INSERT, f"{tk.INSERT}-2c")
        
    def insert_checkbox(self):
        """Insert checkbox"""
        self.text_editor.insert(tk.INSERT, "- [ ] ")
        
    def on_link_start(self, event):
        """Auto-complete for links"""
        # Get current word
        pass  # Simple implementation - can be enhanced
        
    def on_text_change(self, event=None):
        """Handle text changes"""
        self.mark_unsaved()
        self.update_preview()
        self.update_word_count()
        
    def mark_unsaved(self):
        """Mark document as having unsaved changes"""
        if not self.unsaved_changes:
            self.unsaved_changes = True
            title = self.title_var.get()
            if title:
                self.root.title(f"MyNotes - {title}*")
                
    def update_word_count(self):
        """Update word count"""
        content = self.text_editor.get(1.0, tk.END)
        words = len(content.split())
        self.word_count_label.config(text=f"Words: {words}")
        
    def update_tags(self):
        """Update tags for current note"""
        if not self.current_file:
            return
            
        tags = [t.strip() for t in self.tags_entry.get().split(',') if t.strip()]
        self.update_metadata(self.current_file.name, self.title_var.get(), tags)
        self.refresh_notes_list()
        self.update_status("Tags updated")
        
    def update_status(self, message):
        """Update status bar message"""
        self.status_label.config(text=message)
        self.root.after(3000, lambda: self.status_label.config(text="Ready"))
        
    # Theme methods
    
    def toggle_theme(self):
        """Toggle between light and dark theme"""
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.apply_theme()
        
    def apply_theme(self):
        """Apply current theme"""
        if self.current_theme == "dark":
            bg = "#2b2b2b"
            fg = "#e0e0e0"
            select_bg = "#404040"
        else:
            bg = "#ffffff"
            fg = "#000000"
            select_bg = "#e0e0e0"
            
        self.text_editor.config(bg=bg, fg=fg, insertbackground=fg)
        self.preview_text.config(bg=bg, fg=fg)
        
    # Metadata methods
    
    def load_metadata(self):
        """Load metadata from JSON file"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
            except:
                self.metadata = {}
        else:
            self.metadata = {}
            
    def save_metadata(self):
        """Save metadata to JSON file"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            print(f"Failed to save metadata: {e}")
            
    def update_metadata(self, filename, title, tags):
        """Update metadata for a note"""
        self.metadata[filename] = {
            'title': title,
            'tags': tags,
            'modified': datetime.now().isoformat()
        }
        self.save_metadata()
        
    # Utility methods
    
    def sanitize_filename(self, title):
        """Create safe filename from title"""
        # Remove invalid characters
        safe = re.sub(r'[<>:"/\\|?*]', '', title)
        safe = safe.replace(' ', '_')
        return safe[:50]  # Limit length
        
    def show_markdown_guide(self):
        """Show markdown syntax guide"""
        guide = """
Markdown Quick Reference:

# Header 1
## Header 2
### Header 3

**bold text**
*italic text*

- Bullet list item
- Another item

1. Numbered list
2. Another item

[[Link to another note]]

- [ ] Unchecked checkbox
- [x] Checked checkbox

`code`

---
Horizontal line
"""
        messagebox.showinfo("Markdown Guide", guide)
        
    def show_about(self):
        """Show about dialog"""
        about_text = """
MyNotes v1.0

A lightweight, portable note-taking application

Features:
• Markdown support
• Note linking
• Tags and search
• Backlinks
• Dark/Light themes
• 100% portable

All notes stored as plain .md files
        """
        messagebox.showinfo("About MyNotes", about_text)
        
    def exit_app(self):
        """Exit application"""
        if self.unsaved_changes:
            if messagebox.askyesno("Unsaved Changes", "Save before exiting?"):
                self.save_note()
                
        self.root.quit()


def main():
    """Main entry point"""
    root = tk.Tk()
    app = MyNotesApp(root)
    root.protocol("WM_DELETE_WINDOW", app.exit_app)
    root.mainloop()


if __name__ == "__main__":
    main()

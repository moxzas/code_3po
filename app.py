import os
import json
import pyperclip
from tkinter import Tk, filedialog, Listbox, Button, Scrollbar, END, MULTIPLE, VERTICAL, Label, Text, Frame, font

CONFIG_FILENAME = "code3po_config.json"


class ProjectPromptGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Code 3PO: Project Prompt Generator")
        self.project_root = ""
        self.selected_dirs = []
        self.current_files = {}  # Dictionary to map display names to file paths

        # Project Root Frame (Compact Layout)
        root_frame = Frame(self.root)
        root_frame.pack(fill="x", pady=5)
        Label(root_frame, text="Project Root", anchor="w").pack(side="left", padx=5)
        self.project_root_field = Text(root_frame, height=1, wrap="none", width=60)
        self.project_root_field.config(state="disabled")
        self.project_root_field.pack(side="left", padx=5)
        Button(root_frame, text="Reset", command=self.select_project_root).pack(side="left", padx=5)

        # Relevant Directories Frame (Compact Layout)
        dirs_frame = Frame(self.root)
        dirs_frame.pack(fill="x", pady=5)
        Label(dirs_frame, text="Relevant Directories", anchor="w").pack(side="left", padx=5)
        self.relevant_dirs_field = Text(dirs_frame, height=1, wrap="none", width=60)
        self.relevant_dirs_field.config(state="disabled")
        self.relevant_dirs_field.pack(side="left", padx=5)

        # Buttons for relevant directories
        Button(dirs_frame, text="Add", command=self.add_relevant_directory).pack(side="left", padx=5)
        Button(dirs_frame, text="Reset", command=self.reset_relevant_directories).pack(side="left", padx=5)

        # File Listbox with Scrollbar
        self.file_scrollbar = Scrollbar(self.root, orient=VERTICAL)
        self.file_listbox = Listbox(self.root, selectmode=MULTIPLE, yscrollcommand=self.file_scrollbar.set, width=100,
                                    height=40)
        self.file_scrollbar.config(command=self.file_listbox.yview)
        self.file_scrollbar.pack(side="right", fill="y")
        self.file_listbox.pack(pady=5)

        # Set fixed-width font for ASCII display with size 16
        monospace_font = font.Font(family="Courier", size=16)
        self.file_listbox.config(font=monospace_font)

        # Generate Prompt Button
        self.generate_prompt_button = Button(self.root, text="Generate Prompt and Copy to Clipboard",
                                             command=self.generate_prompt)
        self.generate_prompt_button.pack(pady=5)

        # Bind Return/Enter key to the Generate Prompt function
        self.root.bind("<Return>", lambda event: self.generate_prompt())

    def get_config_path(self):
        """Get the path to the configuration file in the current project root."""
        return os.path.join(self.project_root, CONFIG_FILENAME)

    def load_config(self):
        """Load configuration from the project root if available."""
        config_path = self.get_config_path()
        if os.path.exists(config_path):
            with open(config_path, "r") as file:
                return json.load(file)
        return {"project_root": "", "selected_dirs": []}

    def save_config(self):
        """Save configuration to the project root."""
        config_path = self.get_config_path()
        config = {"project_root": self.project_root, "selected_dirs": self.selected_dirs}
        with open(config_path, "w") as file:
            json.dump(config, file, indent=4)

    def select_project_root(self):
        """Select project root directory and load its configuration."""
        project_dir = filedialog.askdirectory(title="Select Project Root")
        if project_dir:
            self.project_root = project_dir
            self.project_root_field.config(state="normal")
            self.project_root_field.delete("1.0", END)
            self.project_root_field.insert("1.0", self.project_root)
            self.project_root_field.config(state="disabled")

            # Load configuration if it exists, otherwise initialize it
            config = self.load_config()
            self.selected_dirs = config.get("selected_dirs", [])
            self.relevant_dirs_field.config(state="normal")
            self.relevant_dirs_field.delete("1.0", END)
            self.relevant_dirs_field.insert("1.0", ", ".join(self.selected_dirs))
            self.relevant_dirs_field.config(state="disabled")

            self.save_config()
            self.refresh_file_list()

    def add_relevant_directory(self):
        """Add a single relevant directory to the configuration."""
        if not self.project_root:
            return

        selected_dir = filedialog.askdirectory(title="Add Relevant Directory", initialdir=self.project_root)
        if selected_dir:
            relative_path = os.path.relpath(selected_dir, self.project_root)
            if relative_path not in self.selected_dirs:
                self.selected_dirs.append(relative_path)
                self.relevant_dirs_field.config(state="normal")
                self.relevant_dirs_field.delete("1.0", END)
                self.relevant_dirs_field.insert("1.0", ", ".join(self.selected_dirs))
                self.relevant_dirs_field.config(state="disabled")
                self.save_config()
                self.refresh_file_list()

    def reset_relevant_directories(self):
        """Reset the relevant directories in the configuration."""
        self.selected_dirs = []
        self.relevant_dirs_field.config(state="normal")
        self.relevant_dirs_field.delete("1.0", END)
        self.relevant_dirs_field.config(state="disabled")
        self.save_config()
        self.refresh_file_list()

    def refresh_file_list(self):
        """Refresh the file list based on the selected directories."""
        self.file_listbox.delete(0, END)
        self.current_files = {}  # Reset current files mapping

        for selected_dir in self.selected_dirs:
            # Add the relevant directory as a top-level node
            self.file_listbox.insert(END, selected_dir)

            full_path = os.path.join(self.project_root, selected_dir)
            if os.path.exists(full_path):
                # Generate the tree structure for the directory
                tree_structure = self.generate_ascii_tree(full_path, selected_dir)
                for display_text, file_path in tree_structure:
                    self.file_listbox.insert(END, f"    {display_text}")  # Indent for hierarchy
                    # Save the file path with its display name as the key
                    self.current_files[display_text.strip()] = file_path

    def generate_ascii_tree(self, dir_path, relative_dir):
        """Generate ASCII tree for a directory with folders first, then files."""
        ascii_tree = []

        def walk_directory(path, prefix=""):
            # Separate folders and files
            items = os.listdir(path)
            folders = sorted([item for item in items if os.path.isdir(os.path.join(path, item))])
            files = sorted([item for item in items if os.path.isfile(os.path.join(path, item))])
            sorted_items = folders + files

            # Walk through sorted items
            for index, item in enumerate(sorted_items):
                item_path = os.path.join(path, item)
                connector = "└── " if index == len(sorted_items) - 1 else "├── "
                relative_path = os.path.relpath(item_path, self.project_root)
                ascii_tree.append((f"{prefix}{connector}{item}", item_path))
                if os.path.isdir(item_path):
                    walk_directory(item_path, prefix + ("    " if index == len(sorted_items) - 1 else "│   "))

        walk_directory(dir_path)
        return ascii_tree

    def generate_prompt(self):
        """Generate prompt text and copy it to the clipboard."""
        selected_indices = self.file_listbox.curselection()
        if not selected_indices:
            return

        # Get selected items from the Listbox
        selected_items = [self.file_listbox.get(i).strip() for i in selected_indices]

        # Map selected items to their file paths
        selected_files = [self.current_files[item] for item in selected_items if item in self.current_files]

        # Read content for each selected file
        prompt_content = []
        for file_path in selected_files:
            try:
                with open(file_path, "r") as file:
                    content = file.read()
                    # Use relative path for output with '>' prefix
                    relative_path = os.path.relpath(file_path, self.project_root)
                    prompt_content.append(f"> {relative_path}\n{content}")
            except Exception as e:
                relative_path = os.path.relpath(file_path, self.project_root)
                prompt_content.append(f"> {relative_path}\nError reading file: {e}")

        # Construct full project structure with relevant directories as top-level nodes
        full_structure = []
        for selected_dir in self.selected_dirs:
            dir_path = os.path.join(self.project_root, selected_dir)
            full_structure.append(selected_dir)  # Add the directory name as a top-level node
            tree_structure = self.generate_ascii_tree(dir_path, selected_dir)
            full_structure.extend(f"    {item[0]}" for item in tree_structure)

        full_tree = "\n".join(full_structure)
        export_text = "\n\n".join(prompt_content) + "\n\n" + f"### Project Structure ###\n" + full_tree

        # Copy to clipboard and print to console
        pyperclip.copy(export_text)
        print(export_text)


if __name__ == "__main__":
    root = Tk()
    app = ProjectPromptGeneratorApp(root)
    root.mainloop()

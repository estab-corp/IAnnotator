from tkinter import messagebox
import tkinter as tk
from typing import Tuple, Optional
from project.project import Project
from project.undo_manager import UndoManager
from annotator.canvas import CanvasImage
from annotator.inspector import AnnotationsInspector
from annotator.inspector_interface import ChangeReason, ChangeDiff


class AnnotatorWindow(tk.Tk):
    def __init__(self, project: Project, **kwargs):
        super().__init__(**kwargs)
        self.undo_manager = UndoManager()
        self.project = project
        self.title(f"Model Annotator file {self.project.folder}")
        self._setup_ui()
        self._setup_menu_bar()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.createcommand("tk::mac::Quit", self.on_closing)

    def on_closing(self, _=None):
        if not self.project.dirty or messagebox.askokcancel("Quit", "Unsaved changes, do you want to quit?"):
            self.destroy()

    def _setup_menu_bar(self):
        menu_bar = tk.Menu(self)

        menu_file = tk.Menu(menu_bar, tearoff=0)
        menu_file.add_command(
            label="Save", command=self.save, accelerator="Command+s")
        self.bind_all("<Command-s>", self.save)

        menu_bar.add_cascade(label="File", menu=menu_file)

        self.edit_menu = tk.Menu(menu_bar, tearoff=0)
        self.edit_menu.add_command(
            label="Undo", command=self.undo, accelerator="Command+z", state="disabled")
        self.bind_all("<Command-z>", self.undo)
        self.edit_menu.add_command(
            label="Redo", command=self.redo, accelerator="Shift+Command+Z")
        self.bind_all("<Shift-Command-Z>", self.redo)
        menu_bar.add_cascade(label="Edit", menu=self.edit_menu)
        self.edit_menu.entryconfig("Redo", state='disabled')

        self.config(menu=menu_bar)

    def save(self, _=None):
        self.project.save_file()

    def _setup_ui(self):
        self.geometry(
            f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}")
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        center = tk.Frame(self, bg='gray2', width=50,
                          height=40, padx=3, pady=3)
        center.grid(row=1, sticky="nsew")
        center.grid_rowconfigure(0, weight=1)
        center.grid_columnconfigure(1, weight=1)

        self.left_panel = tk.Frame(center, bg='blue', width=200, height=190)
        self.inspector = AnnotationsInspector(self, center, bg='green', width=100,
                                              height=190, padx=3, pady=3)
        self.inspector.update_classes_list(self.project.model)
        self.left_panel.grid(row=0, column=0, sticky="ns")
        self.inspector.grid(row=0, column=2, sticky="ns")

        self.canvas = CanvasImage(self, center, bd=2)
        self.canvas.grid(row=0, column=1, sticky="nsew")
        self.listbox = tk.Listbox(
            self.left_panel, selectmode=tk.SINGLE, exportselection=False)
        self.listbox.bind("<<ListboxSelect>>", self.img_selection_changed)
        self.listbox.pack(expand=True, fill='y')
        for i, img in enumerate(self.project.model.images):
            self.listbox.insert(i, img.filename)

    def img_selection_changed(self, _):
        sel_index = self.listbox.curselection()[0]
        img_path = self.project.get_image_path(sel_index)
        self.canvas.show_image(
            img_path, self.project.model.images[sel_index])
        self.inspector.update_inspector(
            self.project.model.images[sel_index])

    def annotations_selection_changed(self, index):
        self.inspector.do_select_annotation(index)
        self.canvas.selected_annotation_idx = index
        self.canvas.draw_annotations()

    def annotations_changed(self, index,  reason: ChangeReason, commit: bool = True, diff: Optional[ChangeDiff] = None):
        self.project.dirty = True
        self.inspector.update_annotation(index)
        self.canvas.draw_annotations()
        self.inspector.update_classes_list(self.project.model)
        if commit:
            self.undo_manager.push_change(UndoManager.Command(
                reason,
                img_index=self.listbox.curselection()[0],
                anno_index=index,
                diff=diff))
            self.edit_menu.entryconfig("Undo", state='active')
            self.edit_menu.entryconfig("Redo", state='disabled')

    def mouse_pos_changed(self, coords: Tuple[int, int]):
        self.inspector.mouse_pos_changed(coords)

    def undo(self, _=None):
        if self.undo_manager.num_prev_commands() == 0:
            self.edit_menu.entryconfig("Undo", state='disabled')
            return
        self.undo_manager.undo(self.project.model)
        self.canvas.draw_annotations()
        sel_index = self.listbox.curselection()[0]
        self.inspector.update_inspector(self.project.model.images[sel_index])
        self.edit_menu.entryconfig("Redo", state='active')
        if self.undo_manager.num_prev_commands() == 0:
            self.edit_menu.entryconfig("Undo", state='disabled')

    def redo(self, _=None):
        self.undo_manager.redo(self.project.model)
        self.canvas.draw_annotations()
        sel_index = self.listbox.curselection()[0]
        self.inspector.update_inspector(self.project.model.images[sel_index])
        self.edit_menu.entryconfig("Undo", state='active')
        if self.undo_manager.num_next_commands() == 0:
            self.edit_menu.entryconfig("Redo", state='disabled')

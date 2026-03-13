from tkinter import messagebox
import tkinter as tk
from typing import Tuple, Optional
from tkinter import filedialog
from project.project import Project
from project.model import Model
from project.undo_manager import UndoManager
from annotator.canvas import CanvasImage
from annotator.inspector import AnnotationsInspector
from annotator.inspector_interface import ChangeReason, ChangeDiff
import os


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
        self.focus_force()

    def on_closing(self, _=None):
        if not self.project.dirty or messagebox.askokcancel("Quit", "Unsaved changes, do you want to quit?"):
            self.destroy()
            return
        self.focus_force()

    def _setup_menu_bar(self):
        menu_bar = tk.Menu(self)

        # file Menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(
            label="Save", command=self.save, accelerator="Command+s")
        self.bind_all("<Command-s>", self.save)
        menu_bar.add_cascade(label="File", menu=file_menu)

        # Edit Menu
        self.edit_menu = tk.Menu(menu_bar, tearoff=0)
        self.edit_menu.add_command(
            label="Undo", command=self.undo, accelerator="Command+z", state="disabled")
        self.bind_all("<Command-z>", self.undo)
        self.edit_menu.add_command(
            label="Redo", command=self.redo, accelerator="Shift+Command+Z")
        self.bind_all("<Shift-Command-Z>", self.redo)
        menu_bar.add_cascade(label="Edit", menu=self.edit_menu)
        self.edit_menu.entryconfig("Redo", state='disabled')
        self.edit_menu.add_separator()
        self.edit_menu.add_command(
            label="Duplicate", command=self.duplicate, accelerator="Command+D")
        self.bind_all("<Command-d>", self.duplicate)
        self.edit_menu.entryconfig("Duplicate", state='disabled')

        # Images Menu
        images_menu = tk.Menu(menu_bar, tearoff=0)
        images_menu.add_command(
            label="New Image", command=self.add_new_image, accelerator="Command+n")
        self.bind_all("<Command-n>", self.add_new_image)
        menu_bar.add_cascade(label="Images", menu=images_menu)

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
        self.update_image_list()

    def update_image_list(self):
        self.listbox.delete(0, tk.END)
        for i, img in enumerate(self.project.model.images):
            self.listbox.insert(i, img.filename)

    def img_selection_changed(self, _):
        sel_index = self.listbox.curselection()[0]
        img_path = self.project.get_image_path(sel_index)
        self.canvas.show_image(
            img_path, self.project.model.images[sel_index])
        self.inspector.update_inspector(
            self.project.model.images[sel_index])
        self.edit_menu.entryconfig("Duplicate", state='active')

    def annotations_selection_changed(self, index):
        self.inspector.do_select_annotation(index)
        self.canvas.selected_annotation_idx = index
        self.canvas.draw_annotations()
        self.edit_menu.entryconfig("Duplicate", state='active')

    def annotations_changed(self, index: int,  reason: ChangeReason, commit: bool = True, diff: Optional[ChangeDiff] = None):
        self.inspector.update_annotation(index)
        self.canvas.draw_annotations()
        self.inspector.update_classes_list(self.project.model)
        if commit:
            was_clean = self.project.dirty is False
            self.project.dirty = True
            self.undo_manager.push_change(UndoManager.Command(
                reason,
                img_index=self.listbox.curselection()[0],
                anno_index=index,
                diff=diff), mark_dirty=was_clean)
            self.edit_menu.entryconfig("Undo", state='active')
            self.edit_menu.entryconfig("Redo", state='disabled')

    def mouse_pos_changed(self, coords: Tuple[int, int]):
        self.inspector.mouse_pos_changed(coords)

    def undo(self, _=None):
        if self.undo_manager.num_prev_commands() == 0:
            self.edit_menu.entryconfig("Undo", state='disabled')
            return
        if self.undo_manager.undo(self.project.model):
            self.project.dirty = False
        self.canvas.draw_annotations()
        img_index = self.listbox.curselection()[0]
        self.inspector.update_inspector(self.project.model.images[img_index])
        self.edit_menu.entryconfig("Redo", state='active')
        if self.undo_manager.num_prev_commands() == 0:
            self.edit_menu.entryconfig("Undo", state='disabled')

    def redo(self, _=None):
        self.undo_manager.redo(self.project.model)
        self.canvas.draw_annotations()
        img_index = self.listbox.curselection()[0]
        self.inspector.update_inspector(self.project.model.images[img_index])
        self.edit_menu.entryconfig("Undo", state='active')
        if self.undo_manager.num_next_commands() == 0:
            self.edit_menu.entryconfig("Redo", state='disabled')

    def duplicate(self, _=None):
        img_index = self.listbox.curselection()[0]
        anno_index = self.inspector.current_annotation_index
        image = self.project.model.images[img_index]
        new_anno = image.annotations[anno_index].copy()
        new_anno.x += 20
        new_anno.y += 20
        image.annotations.append(new_anno)
        diff = ChangeDiff()
        diff.annotation = new_anno
        new_index = len(image.annotations)-1
        self.annotations_changed(
            new_index, reason=ChangeReason.ANNO_ADDED, diff=diff)
        self.inspector.update_annotation_list()
        self.annotations_selection_changed(new_index)

    def add_new_image(self, _=None):
        filenames = filedialog.askopenfilenames(
            title="Add new image", initialdir=self.project.folder)
        self.focus_force()
        if len(filenames) == 0:
            return
        print(f"add image filefilenames={filenames}")
        for filepath in filenames:
            p = os.path.relpath(filepath, self.project.folder)
            print(p)
            new_img = Model.Image()
            new_img.filename = p
            self.project.model.images.append(new_img)
        self.project.dirty = True
        self.update_image_list()

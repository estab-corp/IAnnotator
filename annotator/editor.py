import os
import functools
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Tuple, Optional
from formats import available_formats
from project.project import Project, ProjectWatcher
from project.model import Model
from project.cmd_manager import CommandManager, ChangeReason, ChangeDiff
from annotator.image_tree_widget import ImageTreeWidget
from annotator.canvas import CanvasImage, CanvasWatcher
from annotator.inspector import AnnotationsInspector


class CopyPasteBuffer:
    def __init__(self, annotation: Model.Image.Annotation):
        self.annotation = annotation


class AnnotatorWindow(tk.Tk, ProjectWatcher, CanvasWatcher):
    def __init__(self, project: Project, **kwargs):
        super().__init__(**kwargs)
        self.project = project
        self.project.watchers.append(self)

        self._setup_ui()
        self._setup_menu_bar()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.createcommand("tk::mac::Quit", self.on_closing)
        self.update_title()
        self.focus_force()
        self._copy_buffer: Optional[CopyPasteBuffer] = None

    def update_title(self):
        file_name = self.project.json_file
        if file_name == "":
            file_name = "untitled"
        self.title(f"Model Annotator file '{file_name}'")

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
        self.inspector = AnnotationsInspector(project=self.project, master=center, bg='green', width=100,
                                              height=190, padx=3, pady=3)
        self.inspector.update_classes_list(self.project.model)
        self.left_panel.grid(row=0, column=0, sticky="ns")
        self.inspector.grid(row=0, column=2, sticky="ns")

        self.canvas = CanvasImage(
            project=self.project, watcher=self, master=center, bd=2)
        self.canvas.grid(row=0, column=1, sticky="nsew")
        self.image_tree = ImageTreeWidget(self.left_panel)
        self.image_tree.pack(expand=True, fill='y')
        self.image_tree.bind("<<TreeviewSelect>>", self.img_selection_changed)
        self.image_tree.update_image_list(self.project.model)

    def _setup_menu_bar(self):
        menu_bar = tk.Menu(self)

        # file Menu
        file_menu = tk.Menu(menu_bar, tearoff=0)

        file_menu.add_command(
            label="New", command=self.new, accelerator="Command+n")
        self.bind_all("<Command-n>", self.new)
        file_menu.add_separator()

        file_menu.add_command(
            label="Open", command=self.open, accelerator="Command+o")
        self.bind_all("<Command-o>", self.open)

        file_menu.add_separator()
        file_menu.add_command(
            label="Save", command=self.save, accelerator="Command+s")
        self.bind_all("<Command-s>", self.save)

        save_as_submenu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Save as", menu=save_as_submenu)
        for format_ in available_formats():
            save_as_submenu.add_command(
                label=format_, command=functools.partial(self.save_as, format_))
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
            label="Cut", command=self.cmd_cut, accelerator="Command+x")
        self.bind_all("<Command-x>", self.cmd_cut)
        self.edit_menu.add_command(
            label="Copy", command=self.cmd_copy, accelerator="Command+c")
        self.bind_all("<Command-c>", self.cmd_copy)
        self.edit_menu.add_command(
            label="Paste", command=self.cmd_paste, accelerator="Command+v")
        self.bind_all("<Command-v>", self.cmd_paste)
        self.edit_menu.add_command(
            label="Duplicate", command=self.duplicate_annotation, accelerator="Command+D")
        self.bind_all("<Command-d>", self.duplicate_annotation)

        # Images Menu
        self.images_menu = tk.Menu(menu_bar, tearoff=0)
        self.images_menu.add_command(
            label="New Image", command=self.add_new_image, accelerator="Command+i")
        self.bind_all("<Command-i>", self.add_new_image)
        menu_bar.add_cascade(label="Images", menu=self.images_menu)
        self.images_menu.add_command(
            label="Duplicate Selected", command=self.duplicate_selected_image, accelerator="Shift+Command+D")
        self.bind_all("<Shift-Command-D>", self.duplicate_selected_image)

        self.config(menu=menu_bar)
        self.enable_paste(False)
        self.enable_copy_cut_duplicate(False)
        self.enable_duplicated_selected_image(False)

    def enable_paste(self, state: bool):
        s = 'active' if state else 'disabled'
        self.edit_menu.entryconfig("Paste", state=s)

    def enable_copy_cut_duplicate(self, state: bool):
        s = 'active' if state else 'disabled'
        self.edit_menu.entryconfig("Cut", state=s)
        self.edit_menu.entryconfig("Copy", state=s)
        self.edit_menu.entryconfig("Duplicate", state=s)

    def enable_duplicated_selected_image(self, state: bool):
        s = 'active' if state else 'disabled'
        self.images_menu.entryconfig("Duplicate Selected", state=s)

    def on_closing(self, _=None):
        if self.ask_if_ok_to_loose_changes(is_quit=True):
            self.destroy()

    def ask_if_ok_to_loose_changes(self, is_quit: bool = False) -> bool:
        if self.project.dirty:
            msg = "Unsaved changes, "
            if is_quit:
                msg += "do you want to quit?"
            else:
                msg += "do you want to open a new file?"
            if not messagebox.askokcancel("Quit", msg):
                self.focus_force()
                return False
        self.focus_force()
        return True

    def open(self, _=None):
        if not self.ask_if_ok_to_loose_changes():
            return

        filename = filedialog.askopenfilename(
            title="New project", initialdir=self.project.get_folder())
        self.focus_force()
        if len(filename) == 0:
            return
        with open(filename, encoding="utf-8") as file:
            try:
                model, fmt = Model.load(file, in_format=None)
                if model is None:
                    messagebox.showerror(
                        title="Open error", message="unknown error")
                    return
                project = Project(model)
                project.default_format = fmt
                project.json_file = filename
                self.set_project(project)
            except TypeError as err:
                messagebox.showerror(title="Open error", message=str(err))

    def new(self, _=None):
        if not self.ask_if_ok_to_loose_changes():
            return
        self.set_project(Project.new_default())

    def set_project(self, project: Project):
        self.project = project
        self.project.watchers.append(self)
        self.image_tree.reset()
        self.canvas.project = self.project
        self.inspector.project = self.project
        self.inspector.reset()
        self.canvas.reset()
        file_name = self.project.json_file
        if file_name == "":
            file_name = "untitled"
        self.update_title()
        self.inspector.update_classes_list(self.project.model)
        self.image_tree.update_image_list(self.project.model)
        self.enable_duplicated_selected_image(False)

    def save(self, _=None):
        if self.project.json_file == "":
            filename = filedialog.asksaveasfilename(title="Save project as")
            self.focus_force()
            if filename == "":
                return
            self.project.json_file = filename
        self.update_title()
        self.project.save_file()

    def save_as(self, format_: str):
        filename = filedialog.asksaveasfilename(
            title=f"Save project using {format_}",
            initialdir=self.project.get_folder(),
        )
        self.focus_force()
        if filename == "":
            return
        self.project.save_as_file(filename, format_)

    def img_selection_changed(self, _):
        sel_img_index, sel_anno_index = self.image_tree.get_selected_tuple()
        if sel_img_index == -1:
            self.enable_duplicated_selected_image(False)
            return

        img_path = self.project.get_image_path(sel_img_index)
        img_ok = self.canvas.show_image(
            img_path,  sel_img_index)
        if img_ok is False:
            self.image_tree.mark_invalid_img(sel_img_index)
        self.inspector.update_inspector_image(sel_img_index)
        if sel_anno_index != -1:
            self.annotations_selection_changed(sel_anno_index)
        _, anno_idx = self.image_tree.get_selected_tuple()
        self.enable_copy_cut_duplicate(state=anno_idx != -1)
        self.enable_duplicated_selected_image(True)

    def annotations_selection_changed(self, index):
        self.inspector.do_select_annotation(index)
        self.canvas.select_annotation(index)
        self.edit_menu.entryconfig("Duplicate", state='active')
        self.image_tree.update_selected_annotation(index)

    def annotation_list_changed(self, img_index: int):
        _, anno_idx = self.image_tree.get_selected_tuple()
        self.inspector.update_annotation(anno_idx)
        self.canvas.draw_annotations()
        self.inspector.update_classes_list(self.project.model)
        self.image_tree.update_image_list(self.project.model)

    def canvas_selection_changed(self, anno_idx: int):
        self.image_tree.update_selected_annotation(anno_idx)

    def mouse_pos_changed(self, coords: Tuple[int, int]):
        self.inspector.mouse_pos_changed(coords)

    def annotation_is_changing(self, img_idx: int, anno_idx: int):
        self.inspector.annotation_is_changing(img_idx, anno_idx)

    def annotations_changed(self, anno_index: int,  reason: ChangeReason, commit: bool = True, diff: Optional[ChangeDiff] = None):
        self.inspector.update_annotation(anno_index)
        self.canvas.draw_annotations()
        self.inspector.update_classes_list(self.project.model)

        # need to get this before updating image list
        current_selected_image, _ = self.image_tree.get_selected_tuple()
        self.image_tree.update_image_list(self.project.model)
        if commit:
            was_clean = self.project.dirty is False
            self.project.dirty = True
            self.project.cmd_manager.push_change(CommandManager.Command(
                reason,
                img_index=current_selected_image,
                anno_index=anno_index,
                diff=diff), mark_dirty=was_clean)
            self.edit_menu.entryconfig("Undo", state='active')
            self.edit_menu.entryconfig("Redo", state='disabled')

    def undo(self, _=None):
        if self.project.cmd_manager.num_prev_commands() == 0:
            self.edit_menu.entryconfig("Undo", state='disabled')
            return
        if self.project.cmd_manager.undo(self.project.model):
            self.project.dirty = False
        self.image_tree.update_image_list(self.project.model)
        img_idx, _ = self.image_tree.get_selected_tuple()

        if img_idx != -1:
            self.inspector.update_inspector_image(img_idx)
            self.inspector.update_classes_list(self.project.model)
        self.edit_menu.entryconfig("Redo", state='active')
        if self.project.cmd_manager.num_prev_commands() == 0:
            self.edit_menu.entryconfig("Undo", state='disabled')

    def redo(self, _=None):
        self.project.cmd_manager.redo(self.project.model)
        self.canvas.draw_annotations()
        img_idx, _ = self.image_tree.get_selected_tuple()
        if img_idx != -1:
            self.inspector.update_inspector_image(img_idx)
        self.inspector.update_classes_list(self.project.model)
        self.image_tree.update_image_list(self.project.model)
        self.edit_menu.entryconfig("Undo", state='active')
        if self.project.cmd_manager.num_next_commands() == 0:
            self.edit_menu.entryconfig("Redo", state='disabled')

    def duplicate_annotation(self, _=None):
        img_idx, _ = self.image_tree.get_selected_tuple()
        anno_index = self.inspector.current_annotation_index
        self.project.duplicate_annotation(img_idx=img_idx, anno_idx=anno_index)
        image = self.project.model.images[img_idx]
        new_index = len(image.annotations)-1
        self.annotations_selection_changed(new_index)

    def remove_selected_anno(self):
        img_idx, anno_idx = self.image_tree.get_selected_tuple()
        self.project.remove_annotation(img_idx, anno_idx)

    def cmd_cut(self, _=None):
        img_idx, anno_idx = self.image_tree.get_selected_tuple()
        self._copy_buffer = CopyPasteBuffer(
            self.project.model.images[img_idx].annotations[anno_idx])
        self.enable_paste(True)
        self.remove_selected_anno()

    def cmd_copy(self, _=None):
        img_idx, anno_idx = self.image_tree.get_selected_tuple()
        self._copy_buffer = CopyPasteBuffer(
            self.project.model.images[img_idx].annotations[anno_idx])
        self.enable_paste(True)

    def cmd_paste(self, _=None):
        if self._copy_buffer is None:
            return
        new_anno = self._copy_buffer.annotation.copy()
        new_anno.x += 30
        new_anno.y += 30
        img_idx, _ = self.image_tree.get_selected_tuple()
        image = self.project.model.images[img_idx]
        image.annotations.append(new_anno)
        diff = ChangeDiff()
        diff.annotation = new_anno
        new_index = len(image.annotations)-1
        self.annotations_changed(
            new_index, reason=ChangeReason.ANNO_ADDED, diff=diff)
        self.annotations_selection_changed(new_index)

    def duplicate_selected_image(self, _=None):
        img_idx, _ = self.image_tree.get_selected_tuple()
        assert img_idx != -1
        new_img_idx = self.project.duplicate_image(img_idx)
        self.image_tree.update_image_list(self.project.model)
        self.image_tree.select_image_index(new_img_idx)

    def add_new_image(self, _=None):
        filenames = filedialog.askopenfilenames(
            title="Add new image", initialdir=self.project.get_folder())
        self.focus_force()
        if len(filenames) == 0:
            return
        for filepath in filenames:
            p = os.path.relpath(filepath, self.project.get_folder())
            self.project.add_image(p)
        self.project.dirty = True
        self.image_tree.update_image_list(self.project.model)
        self.image_tree.select_image_index(len(self.project.model.images)-1)

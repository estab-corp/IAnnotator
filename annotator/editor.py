import os
import functools
from tkinter import messagebox
import tkinter as tk
from tkinter import filedialog
from typing import Tuple, Optional
from formats import available_formats
from project.project import Project, ProjectWatcher
from project.model import Model
from project.undo_manager import UndoManager, ChangeReason, ChangeDiff
from annotator.image_tree_widget import ImageTreeWidget
from annotator.canvas import CanvasImage, CanvasWatcher
from annotator.inspector import AnnotationsInspector
from trainer.editor import show_train_win


class CopyPasteBuffer:
    def __init__(self, annotation: Model.Image.Annotation):
        self.annotation = annotation


class AnnotatorWindow(tk.Tk, ProjectWatcher, CanvasWatcher):
    def __init__(self, project: Project, **kwargs):
        super().__init__(**kwargs)
        self.project = project
        self.project.watchers.append(self)
        self.title(f"Model Annotator file {self.project.folder}")
        self._setup_ui()
        self._setup_menu_bar()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.createcommand("tk::mac::Quit", self.on_closing)
        self.focus_force()
        self._copy_buffer: Optional[CopyPasteBuffer] = None
        self.trainer_win = None

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
        self.edit_menu.entryconfig("Paste", state='disabled')
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

        # Train Menu
        model_menu = tk.Menu(menu_bar, tearoff=0)
        model_menu.add_command(
            label="Train", command=self.create_train_win)
        menu_bar.add_cascade(label="Model", menu=model_menu)

        self.config(menu=menu_bar)

    def on_closing(self, _=None):
        if not self.project.dirty or messagebox.askokcancel("Quit", "Unsaved changes, do you want to quit?"):
            self.destroy()
            return
        self.focus_force()

    def create_train_win(self, _=None):
        if self.trainer_win is not None:
            self.trainer_win.lift()
            return
        self.trainer_win = show_train_win(self, self.project)

        def unset_trainer_win(_):
            self.trainer_win = None
        self.trainer_win.bind("<Destroy>", unset_trainer_win)

    def save(self, _=None):
        if self.project.json_file == "":
            filename = filedialog.asksaveasfilename(title="Save project as")
            self.focus_force()
            if filename == "":
                return
            self.project.json_file = filename
        self.project.save_file()

    def save_as(self, format_: str):
        print("save as ", format_)
        filename = filedialog.asksaveasfilename(
            title=f"Save project using {format_}",
            initialdir=self.project.folder,
        )
        self.focus_force()
        if filename == "":
            return
        self.project.save_as_file(filename, format_)

    def img_selection_changed(self, _):
        sel_img_index, sel_anno_index = self.image_tree.get_selected_tuple()
        img_path = self.project.get_image_path(sel_img_index)
        self.canvas.show_image(
            img_path,  sel_img_index)
        self.inspector.update_inspector_image(sel_img_index)
        if sel_anno_index != -1:
            self.annotations_selection_changed(sel_anno_index)
        _, anno_idx = self.image_tree.get_selected_tuple()
        copy_state = "active" if anno_idx != -1 else "disabled"
        self.edit_menu.entryconfig("Duplicate", state=copy_state)
        self.edit_menu.entryconfig("Cut", state=copy_state)
        self.edit_menu.entryconfig("Copy", state=copy_state)

    def annotations_selection_changed(self, index):
        self.inspector.do_select_annotation(index)
        self.canvas.selected_annotation_idx = index
        self.canvas.draw_annotations()
        self.edit_menu.entryconfig("Duplicate", state='active')
        self.image_tree.update_selected_annotation(index)

    def annotation_list_changed(self, img_index: int):
        print(f"Editor.Watcher.annotation_list_changed img_index={img_index}")
        _, anno_idx = self.image_tree.get_selected_tuple()
        self.inspector.update_annotation(anno_idx)
        self.canvas.draw_annotations()
        self.inspector.update_classes_list(self.project.model)
        self.image_tree.update_image_list(self.project.model)

    def canvas_selection_changed(self, anno_idx: int):
        print(f"canvas_selection_changed anno_idx={anno_idx}")
        self.image_tree.update_selected_annotation(anno_idx)

    def mouse_pos_changed(self, coords: Tuple[int, int]):
        self.inspector.mouse_pos_changed(coords)

    def annotation_is_changing(self, img_idx: int, anno_idx: int):
        self.inspector.annotation_is_changing(img_idx, anno_idx)

    def annotations_changed(self, index: int,  reason: ChangeReason, commit: bool = True, diff: Optional[ChangeDiff] = None):
        self.inspector.update_annotation(index)
        self.canvas.draw_annotations()
        self.inspector.update_classes_list(self.project.model)

        # need to get this before updating image list
        current_selected_image, _ = self.image_tree.get_selected_tuple()
        self.image_tree.update_image_list(self.project.model)
        if commit:
            was_clean = self.project.dirty is False
            self.project.dirty = True
            self.project.undo_manager.push_change(UndoManager.Command(
                reason,
                img_index=current_selected_image,
                anno_index=index,
                diff=diff), mark_dirty=was_clean)
            self.edit_menu.entryconfig("Undo", state='active')
            self.edit_menu.entryconfig("Redo", state='disabled')

    def undo(self, _=None):
        if self.project.undo_manager.num_prev_commands() == 0:
            self.edit_menu.entryconfig("Undo", state='disabled')
            return
        if self.project.undo_manager.undo(self.project.model):
            self.project.dirty = False
        self.canvas.draw_annotations()
        img_idx, _ = self.image_tree.get_selected_tuple()
        self.inspector.update_inspector_image(img_idx)
        self.image_tree.update_image_list(self.project.model)
        self.edit_menu.entryconfig("Redo", state='active')
        if self.project.undo_manager.num_prev_commands() == 0:
            self.edit_menu.entryconfig("Undo", state='disabled')

    def redo(self, _=None):
        self.project.undo_manager.redo(self.project.model)
        self.canvas.draw_annotations()
        img_idx, _ = self.image_tree.get_selected_tuple()
        self.inspector.update_inspector_image(img_idx)
        self.image_tree.update_image_list(self.project.model)
        self.edit_menu.entryconfig("Undo", state='active')
        if self.project.undo_manager.num_next_commands() == 0:
            self.edit_menu.entryconfig("Redo", state='disabled')

    def duplicate(self, _=None):
        img_idx, _ = self.image_tree.get_selected_tuple()
        anno_index = self.inspector.current_annotation_index
        self.project.duplicate_annotation(img_idx=img_idx, anno_idx=anno_index)

    def remove_selected_anno(self):
        img_idx, anno_idx = self.image_tree.get_selected_tuple()
        self.project.remove_annotation(img_idx, anno_idx)

    def cmd_cut(self, _=None):
        img_idx, anno_idx = self.image_tree.get_selected_tuple()
        print(f"Cut img_idx={img_idx} anno_idx={anno_idx}")
        self._copy_buffer = CopyPasteBuffer(
            self.project.model.images[img_idx].annotations[anno_idx])
        self.edit_menu.entryconfig("Paste", state='active')
        self.remove_selected_anno()

    def cmd_copy(self, _=None):
        img_idx, anno_idx = self.image_tree.get_selected_tuple()
        self._copy_buffer = CopyPasteBuffer(
            self.project.model.images[img_idx].annotations[anno_idx])
        self.edit_menu.entryconfig("Paste", state='active')

    def cmd_paste(self, _=None):
        if self._copy_buffer is None:
            return
        new_anno = self._copy_buffer.annotation.copy()
        img_idx, _ = self.image_tree.get_selected_tuple()
        image = self.project.model.images[img_idx]
        image.annotations.append(new_anno)
        diff = ChangeDiff()
        diff.annotation = new_anno
        new_index = len(image.annotations)-1
        self.annotations_changed(
            new_index, reason=ChangeReason.ANNO_ADDED, diff=diff)
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
        self.image_tree.update_image_list(self.project.model)
        self.image_tree.select_image_index(len(self.project.model.images)-1)

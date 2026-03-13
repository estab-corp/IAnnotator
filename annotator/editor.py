import os
import functools
from tkinter import messagebox
import tkinter as tk
from tkinter import ttk
from typing import Tuple, Optional, List
from tkinter import filedialog
from formats import available_formats
from project.project import Project
from project.model import Model
from project.undo_manager import UndoManager
from annotator.canvas import CanvasImage
from annotator.inspector import AnnotationsInspector
from annotator.inspector_interface import ChangeReason, ChangeDiff
import bisect


def find_closest_index(lst: List[int], val: int):
    i = bisect.bisect_left(lst, val)
    if i >= len(lst):
        i = len(lst) - 1
    elif i and lst[i] - val > val - lst[i - 1]:
        i = i - 1
    return i


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
        self.image_tree = ttk.Treeview(self.left_panel)
        self.image_tree.pack(expand=True, fill='y')
        self.image_tree.bind("<<TreeviewSelect>>", self.img_selection_changed)
        self.update_image_list()

    def _get_closest_img_selection(self, sel_img: int, sel_anno: int):
        if sel_img == -1:
            return
        # if sel_anno has disappeared, likely due to being remove,
        # we try and get the previous annotation index. If no lower index, selected the parent image
        img_item_index = f"I{sel_img}"
        self.image_tree.item(img_item_index, open=True)
        anno_items = self.image_tree.get_children(img_item_index)

        item_to_select = ""
        if len(anno_items) == 0:
            item_to_select = img_item_index
        else:
            indexes: List[int] = []
            for item in anno_items:
                anno_idx = int(item[1:].split(":")[0])
                indexes.append(anno_idx)
            indexes = sorted(indexes)  # not sure if indexes are sorted
            next_sel_anno = find_closest_index(indexes, sel_anno)
            item_to_select = f"A{next_sel_anno}:"+img_item_index

        if item_to_select != "":
            self.image_tree.selection_set(item_to_select)

    def update_image_list(self):
        sel_img, sel_anno = self.get_selected_tuple()
        self.image_tree.delete(*self.image_tree.get_children())
        for i, img in enumerate(self.project.model.images):
            item = self.image_tree.insert(
                "", tk.END, text=img.filename, iid=f"I{i}")
            for anno_i, anno in enumerate(img.annotations):
                self.image_tree.insert(
                    item, tk.END, text=anno.label, iid=f"A{anno_i}:I{i}")
        if sel_img == -1:
            return
        self._get_closest_img_selection(sel_img, sel_anno)

    def _get_index_from_image_iid(self, item_iid: str):
        assert item_iid.startswith("I")
        return int(item_iid[1:])

    def get_selected_tuple(self) -> Tuple[int, int]:
        if len(self.image_tree.selection()) == 0:
            return (-1, -1)
        item_iid: str = self.image_tree.selection()[0]
        parent_iid: str = self.image_tree.parent(item_iid)
        if parent_iid == "":
            return (self._get_index_from_image_iid(item_iid), -1)
        sel_image = self._get_index_from_image_iid(parent_iid)
        assert item_iid.startswith("A")  # this is an annotation
        sel_anno = int(item_iid[1:].split(":")[0])
        return (sel_image, sel_anno)

    def get_selected_image_index(self) -> int:
        item_iid: str = self.image_tree.selection()[0]
        parent_iid = self.image_tree.parent(item_iid)
        if item_iid.startswith("I"):  # this is an image
            assert parent_iid == ""
            return self._get_index_from_image_iid(item_iid)
        assert item_iid.startswith("A")  # this is an annotation
        return self._get_index_from_image_iid(parent_iid)

    def img_selection_changed(self, _):
        sel_img_index, sel_anno_index = self.get_selected_tuple()
        img_path = self.project.get_image_path(sel_img_index)
        self.canvas.show_image(
            img_path, self.project.model.images[sel_img_index])
        self.inspector.update_inspector(
            self.project.model.images[sel_img_index])
        self.edit_menu.entryconfig("Duplicate", state='active')
        if sel_anno_index != -1:
            self.annotations_selection_changed(sel_anno_index)

    def annotations_selection_changed(self, index):
        self.inspector.do_select_annotation(index)
        self.canvas.selected_annotation_idx = index
        self.canvas.draw_annotations()
        self.edit_menu.entryconfig("Duplicate", state='active')

    def annotations_changed(self, index: int,  reason: ChangeReason, commit: bool = True, diff: Optional[ChangeDiff] = None):
        self.inspector.update_annotation(index)
        self.canvas.draw_annotations()
        self.inspector.update_classes_list(self.project.model)

        # need to get this before updating image list
        current_selected_image = self.get_selected_image_index()
        self.update_image_list()
        if commit:
            was_clean = self.project.dirty is False
            self.project.dirty = True
            self.undo_manager.push_change(UndoManager.Command(
                reason,
                img_index=current_selected_image,
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
        img_index = self.get_selected_image_index()
        self.inspector.update_inspector(self.project.model.images[img_index])
        self.edit_menu.entryconfig("Redo", state='active')
        if self.undo_manager.num_prev_commands() == 0:
            self.edit_menu.entryconfig("Undo", state='disabled')

    def redo(self, _=None):
        self.undo_manager.redo(self.project.model)
        self.canvas.draw_annotations()
        img_index = self.get_selected_image_index()
        self.inspector.update_inspector(self.project.model.images[img_index])
        self.edit_menu.entryconfig("Undo", state='active')
        if self.undo_manager.num_next_commands() == 0:
            self.edit_menu.entryconfig("Redo", state='disabled')

    def duplicate(self, _=None):
        img_index = self.get_selected_image_index()
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

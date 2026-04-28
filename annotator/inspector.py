import tkinter as tk
from typing import Optional, Tuple, Set, Callable
from project.model import Model
from project.project import Project
from project.undo_manager import ChangeReason, ChangeDiff

SPIN_BOX_INCREMENT = 1


class ClassListOptionMenu(tk.OptionMenu):
    def __init__(self, parent, value_changed: Callable[[str], None]):
        self.classes = [""]
        self.value_changed = value_changed
        self.om_variable = tk.StringVar(parent)
        super().__init__(parent, self.om_variable, *self.classes)
        self.om_variable.trace("w", self._changed)
        self.om_variable.set("")

    def _changed(self, *_):
        if self.value_changed and len(self.om_variable.get()) > 0:
            self.value_changed(self.om_variable.get())

    def reset(self):
        self.update_list(set())

    def update_list(self, classes: Set[str]):
        self.classes = list(classes)
        menu = self["menu"]
        menu.delete(0, "end")
        for string in self.classes:
            menu.add_command(label=string,
                             command=lambda value=string: self.om_variable.set(value))


class AnnotationsInspector(tk.Frame):
    def __init__(self, project: Project, master: tk.Tk, **kwargs):
        super().__init__(master, **kwargs)
        self.project = project
        self.current_img_idx: int = -1
        self.current_image: Optional[Model.Image] = None
        self.current_annotation_index = -1

        # annotation frame
        self.annotations_frame = tk.LabelFrame(self, text="annotations")
        self.annotations_frame.pack(
            padx=10, pady=10, fill="both")  # , expand="yes")

        btton = tk.Button(self.annotations_frame,
                          text="add", command=self.add_new)

        btton.grid(row=0, column=0)

        tk.Label(self.annotations_frame, text="x: ").grid(row=2, column=0)
        self.x_val = tk.IntVar(value=0)
        tk.Spinbox(self.annotations_frame, textvariable=self.x_val, from_=0, to=2000,
                   increment=SPIN_BOX_INCREMENT, command=self.x_changed).grid(row=2, column=1)

        tk.Label(self.annotations_frame, text="y: ").grid(row=3, column=0)
        self.y_val = tk.IntVar(value=0)
        tk.Spinbox(self.annotations_frame, textvariable=self.y_val, from_=0, to=2000,
                   increment=SPIN_BOX_INCREMENT, command=self.y_changed).grid(row=3, column=1)

        tk.Label(self.annotations_frame, text="w: ").grid(row=4, column=0)
        self.w_val = tk.IntVar(value=0)
        tk.Spinbox(self.annotations_frame, textvariable=self.w_val, from_=0, to=2000,
                   increment=SPIN_BOX_INCREMENT, command=self.w_changed).grid(row=4, column=1)

        tk.Label(self.annotations_frame, text="h: ").grid(row=5, column=0)
        self.h_val = tk.IntVar(value=0)
        tk.Spinbox(self.annotations_frame, textvariable=self.h_val, from_=0, to=2000,
                   increment=SPIN_BOX_INCREMENT, command=self.h_changed).grid(row=5, column=1)

        tk.Label(self.annotations_frame, text="label: ").grid(row=6, column=0)
        self.lbl_val = tk.StringVar(value="")
        self.label_entry = tk.Entry(
            self.annotations_frame, textvariable=self.lbl_val, )
        self.label_entry.grid(row=6, column=1)
        self.label_entry.bind("<Return>", self.do_update_label)

        self.classes_option_menu = ClassListOptionMenu(
            self.annotations_frame, self.class_option_changed)
        self.classes_option_menu.grid(row=6, column=2)
        del_btton = tk.Button(self.annotations_frame,
                              text="remove", command=self.remove_anno)
        del_btton.grid(row=7, column=1)

        # image frame
        self.img_info_frame = tk.LabelFrame(self, text="Image")
        self.img_info_frame.pack(padx=10, pady=10, fill="both")

        self.img_size_val = tk.StringVar()
        label = tk.Label(self.img_info_frame,
                         textvariable=self.img_size_val)
        label.pack(padx=5, pady=5)

        self.mouse_pos_val = tk.StringVar()
        label = tk.Label(self.img_info_frame,
                         textvariable=self.mouse_pos_val)
        label.pack(padx=5, pady=5)

        # classes frame
        self.class_info_frame = tk.LabelFrame(self, text="Classes")
        self.class_info_frame.pack(padx=10, pady=10, fill="both")
        self.classes_listbox = tk.Listbox(
            self.class_info_frame, selectmode=tk.SINGLE, exportselection=False)
        self.classes_listbox.grid(row=1, column=1)
        self.reset()

    def reset(self):
        self.mouse_pos_val.set(value="x=? y=?")
        self.img_size_val.set(value="w=? h=?")
        self.x_val.set(value=0)
        self.y_val.set(value=0)
        self.w_val.set(value=0)
        self.h_val.set(value=0)
        self.lbl_val.set(value="")
        self.classes_option_menu.reset()
        self.classes_listbox.delete(0, tk.END)

    def _has_image_and_annotation_selected(self) -> bool:
        return self.current_image is not None and self.current_annotation_index >= 0

    def x_changed(self):
        if not self._has_image_and_annotation_selected():
            return
        prev_x = self.current_image.annotations[self.current_annotation_index].x
        new_x = self.x_val.get()
        self.current_image.annotations[self.current_annotation_index].x = new_x
        diff = ChangeDiff()
        diff.x = new_x - prev_x
        self.project.update_annotation(
            self.current_img_idx, anno_idx=self.current_annotation_index, reason=ChangeReason.ANNO_GEOMETRY, diff=diff)

    def y_changed(self):
        if not self._has_image_and_annotation_selected():
            return
        prev_y = self.current_image.annotations[self.current_annotation_index].y
        new_y = self.y_val.get()
        self.current_image.annotations[self.current_annotation_index].y = new_y
        diff = ChangeDiff()
        diff.y = new_y - prev_y
        self.project.update_annotation(
            self.current_img_idx, anno_idx=self.current_annotation_index, reason=ChangeReason.ANNO_GEOMETRY, diff=diff)

    def w_changed(self):
        if not self._has_image_and_annotation_selected():
            return
        prev_w = self.current_image.annotations[self.current_annotation_index].width
        new_w = self.w_val.get()
        self.current_image.annotations[self.current_annotation_index].width = new_w
        diff = ChangeDiff()
        diff.w = new_w - prev_w
        self.project.update_annotation(
            self.current_img_idx, anno_idx=self.current_annotation_index, reason=ChangeReason.ANNO_GEOMETRY, diff=diff)

    def h_changed(self):
        if not self._has_image_and_annotation_selected():
            return
        prev_h = self.current_image.annotations[self.current_annotation_index].height
        new_h = self.h_val.get()
        self.current_image.annotations[self.current_annotation_index].height = new_h
        diff = ChangeDiff()
        diff.h = new_h - prev_h
        self.project.update_annotation(
            self.current_img_idx, anno_idx=self.current_annotation_index, reason=ChangeReason.ANNO_GEOMETRY, diff=diff)

    def update_classes_list(self, model: Model):
        self.classes_option_menu.update_list(model.get_classes())
        self.classes_listbox.delete(0, tk.END)
        for i, cls in enumerate(model.get_classes()):
            self.classes_listbox.insert(i, cls)

    def remove_anno(self, _=None):
        self.project.remove_annotation(
            img_idx=self.current_img_idx, anno_idx=self.current_annotation_index)

    def do_update_label(self, _=None):
        if not self._has_image_and_annotation_selected():
            return
        self.update_label(self.lbl_val.get())

    def update_label(self, label: str):
        diff = ChangeDiff()
        diff.new_label = label
        diff.prev_label = self.current_image.annotations[self.current_annotation_index].label
        self.current_image.annotations[self.current_annotation_index].label = label

        self.project.update_annotation(
            self.current_img_idx, anno_idx=self.current_annotation_index, reason=ChangeReason.LABEL, diff=diff)

    def class_option_changed(self, value: str):
        self.update_label(value)

    def update_inspector_image(self, img_idx: int):
        self.current_img_idx = img_idx
        self.current_image = self.project.model.images[img_idx]
        self.img_size_val.set(
            f"w={self.current_image.loaded_width} h={self.current_image.loaded_height}")

    def do_select_annotation(self, index: int):
        self.current_annotation_index = index
        self.update_annotation(index)

    def update_annotation(self, index: int):
        if index == -1 or self.current_image is None or index >= len(self.current_image.annotations):
            self.x_val.set(0)
            self.y_val.set(0)
            self.w_val.set(0)
            self.h_val.set(0)
            self.lbl_val.set("")
            return
        self.x_val.set(self.current_image.annotations[index].x)
        self.y_val.set(self.current_image.annotations[index].y)
        self.w_val.set(self.current_image.annotations[index].width)
        self.h_val.set(self.current_image.annotations[index].height)
        self.lbl_val.set(self.current_image.annotations[index].label)

    def add_new(self):
        if self.current_image is None:
            return
        anno = Model.Image.Annotation()
        anno.x = 100
        anno.y = 200
        anno.width = 300
        anno.height = 400
        anno.label = "label"
        self.project.add_annotation(
            img_idx=self.current_img_idx, annotation=anno)
        new_index = len(self.current_image.annotations)-1
        self.do_select_annotation(new_index)

    def mouse_pos_changed(self, coords: Tuple[int, int]):
        self.mouse_pos_val.set(f"x={int(coords[0])} y={int(coords[1])}")

    def annotation_is_changing(self, img_idx: int, anno_idx: int):
        assert img_idx == self.current_img_idx
        self.update_annotation(anno_idx)

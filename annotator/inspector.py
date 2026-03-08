import tkinter as tk
from typing import Optional, Tuple
from model import Model
from annotator.inspector_interface import InspectorInterface


class AnnotationsInspector(tk.Frame):
    def __init__(self, inspector: InspectorInterface, master: tk.Tk, **kwargs):
        super().__init__(master, **kwargs)
        self.inspector = inspector
        self.current_image: Optional[Model.Image] = None
        self.current_annotation_index = -1

        # annotation frame
        self.annotations_frame = tk.LabelFrame(self, text="annotations")
        self.annotations_frame.pack(
            padx=10, pady=10, fill="both")  # , expand="yes")

        btton = tk.Button(self.annotations_frame,
                          text="add", command=self.add_new)

        btton.grid(row=0, column=0)
        self.anno_listbox = tk.Listbox(
            self.annotations_frame, selectmode=tk.SINGLE, exportselection=False)
        self.anno_listbox.grid(row=1, column=1)
        self.anno_listbox.bind("<<ListboxSelect>>", self.selection_changed)

        tk.Label(self.annotations_frame, text="x: ").grid(row=2, column=0)
        self.x_val = tk.IntVar(value=0)
        tk.Spinbox(self.annotations_frame, textvariable=self.x_val, from_=0, to=2000,
                   increment=1).grid(row=2, column=1)

        tk.Label(self.annotations_frame, text="y: ").grid(row=3, column=0)
        self.y_val = tk.IntVar(value=0)
        tk.Spinbox(self.annotations_frame, textvariable=self.y_val, from_=0, to=2000,
                   increment=1).grid(row=3, column=1)

        tk.Label(self.annotations_frame, text="w: ").grid(row=4, column=0)
        self.w_val = tk.IntVar(value=0)
        tk.Spinbox(self.annotations_frame, textvariable=self.w_val, from_=0, to=2000,
                   increment=1).grid(row=4, column=1)

        tk.Label(self.annotations_frame, text="h: ").grid(row=5, column=0)
        self.h_val = tk.IntVar(value=0)
        tk.Spinbox(self.annotations_frame, textvariable=self.h_val, from_=0, to=2000,
                   increment=1).grid(row=5, column=1)

        tk.Label(self.annotations_frame, text="label: ").grid(row=6, column=0)
        self.lbl_val = tk.StringVar(value="Label")
        self.label_entry = tk.Entry(
            self.annotations_frame, textvariable=self.lbl_val, )
        self.label_entry.grid(row=6, column=1)
        self.label_entry.bind("<Return>", self.update_label)

        del_btton = tk.Button(self.annotations_frame,
                              text="remove", command=self.remove_anno)
        del_btton.grid(row=7, column=1)

        # image frame
        self.img_info_frame = tk.LabelFrame(self, text="Image")
        self.img_info_frame.pack(padx=10, pady=10, fill="both")

        self.img_size_val = tk.StringVar(value="w=? h=?")
        label = tk.Label(self.img_info_frame,
                         textvariable=self.img_size_val)
        label.pack(padx=5, pady=5)

        self.mouse_pos_val = tk.StringVar(value="x=? y=?")
        label = tk.Label(self.img_info_frame,
                         textvariable=self.mouse_pos_val)
        label.pack(padx=5, pady=5)

        # classes frame
        self.class_info_frame = tk.LabelFrame(self, text="Classes")
        self.class_info_frame.pack(padx=10, pady=10, fill="both")
        self.classes_listbox = tk.Listbox(
            self.class_info_frame, selectmode=tk.SINGLE, exportselection=False)
        self.classes_listbox.grid(row=1, column=1)

    def update_classes_list(self, model: Model):
        self.classes_listbox.delete(0, tk.END)
        for i, cls in enumerate(model.get_classes()):
            self.classes_listbox.insert(i, cls)

    def remove_anno(self, _=None):
        del self.current_image.annotations[self.current_annotation_index]
        if self.current_annotation_index >= 1:
            self.current_annotation_index -= 1
        if len(self.current_image.annotations) == 0:
            self.current_annotation_index = -1
        self.update_annotation_list()
        self.inspector.annotations_changed(self.current_annotation_index)

    def update_label(self, _=None):
        self.current_image.annotations[self.current_annotation_index].label = self.lbl_val.get(
        )
        self.update_annotation_list()
        self.inspector.annotations_changed(self.current_annotation_index)

    def update_annotation_list(self):
        self.anno_listbox.delete(0, tk.END)
        for i, anno in enumerate(self.current_image.annotations):
            self.anno_listbox.insert(i, f"{anno.label}-{i}")
        if len(self.current_image.annotations) > 0:
            self.do_select_annotation(0)

    def update_inspector(self, image: Model.Image, img_w: int, img_h: int):
        self.current_image = image
        self.img_size_val.set(f"w={img_w} h={img_h}")
        self.update_annotation_list()

    def selection_changed(self, _=None):
        sel_index = self.anno_listbox.curselection()[0]
        self.update_annotation(sel_index)

    def do_select_annotation(self, index: int):
        self.anno_listbox.select_clear(0, tk.END)
        self.current_annotation_index = index
        self.anno_listbox.select_set(index)
        self.update_annotation(index)

    def update_annotation(self, index: int):
        if index == -1:
            self.x_val.set(0)
            self.y_val.set(0)
            self.w_val.set(0)
            self.h_val.set(0)
            self.lbl_val.set("")
            return
        if self.current_image is None:
            return
        self.x_val.set(self.current_image.annotations[index].x)
        self.y_val.set(self.current_image.annotations[index].y)
        self.w_val.set(self.current_image.annotations[index].width)
        self.h_val.set(self.current_image.annotations[index].height)
        self.lbl_val.set(self.current_image.annotations[index].label)

    def add_new(self):
        assert (self.current_image)
        self.current_image.annotations.append(Model.Image.Annotation())
        self.update_annotation_list()
        self.inspector.annotations_changed(
            len(self.current_image.annotations)-1)

    def mouse_pos_changed(self, coords: Tuple[int, int]):
        self.mouse_pos_val.set(f"x={int(coords[0])} y={int(coords[1])}")

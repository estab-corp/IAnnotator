import PIL.Image
import tkinter as tk
from PIL import ImageTk
from typing import List, Optional
from project import Project
from model import Model
HANDLE_SIZE = 10


class InspectorInterface:
    def annotations_selection_changed(self, index):
        pass

    def annotations_changed(self, index):
        pass


class CanvasImage(tk.Canvas):
    def __init__(self, inspector: InspectorInterface, master: tk.Tk, **kwargs):
        super().__init__(master, **kwargs)
        self.inspector = inspector
        self.ratio = 1
        self.source_image = None
        self.image_id = None
        self.image = None
        self.selected_annotation_idx = -1
        self.move_origin_offset = (0, 0)
        self.is_resizing = False
        self.annotations: List[Model.Image.Annotation] = []
        self.rect_ids = []
        self.text_ids = []
        self.handle_ids = []
        self.width, self.height = 0, 0
        self.center_x, self.center_y = 0, 0
        self.bind('<Configure>', self.update_values)
        self.bind('<Button-1>', self.on_click)
        self.bind('<B1-Motion>', self.on_move)

    def on_move(self, event):
        if self.selected_annotation_idx < 0:
            return
        annotation = self.annotations[self.selected_annotation_idx]
        real_x = event.x/self.ratio
        real_y = event.y/self.ratio
        if self.is_resizing:
            annotation.width = real_x-annotation.x
            annotation.height = real_y-annotation.y
        else:
            annotation.x = real_x - self.move_origin_offset[0]
            annotation.y = real_y - self.move_origin_offset[1]

        self.inspector.annotations_changed(self.selected_annotation_idx)
        self.draw_annotations()

    def on_click(self, event):
        self.selected_annotation_idx = -1
        for a_id, annotation in enumerate(self.annotations):
            x = annotation.x*self.ratio
            y = annotation.y*self.ratio
            w = annotation.width*self.ratio
            h = annotation.height*self.ratio

            h_x = x+w
            h_y = y+h
            h_size = HANDLE_SIZE/2
            if h_x-h_size <= event.x <= h_x+h_size and h_y-h_size <= event.y <= h_y+h_size:
                self.selected_annotation_idx = a_id
                self.is_resizing = True
                self.draw_annotations()
                self.inspector.annotations_selection_changed(a_id)
                return
            if x <= event.x <= x+w and y <= event.y <= y+h:
                self.selected_annotation_idx = a_id
                self.is_resizing = False
                self.draw_annotations()
                self.inspector.annotations_selection_changed(a_id)
                self.move_origin_offset = (
                    event.x/self.ratio - annotation.x, event.y/self.ratio - annotation.y)
                return

    def update_values(self, *_):
        self.width = self.winfo_width()
        self.height = self.winfo_height()
        self.center_x = self.width//2
        self.center_y = self.height//2

        if self.image is None:
            return
        self.delete_previous_image()
        self.resize_image()
        self.paste_image()
        self.draw_annotations()

    def delete_previous_image(self):
        if self.image is None:
            return
        self.delete(self.image_id)
        self.image = self.image_id = None

    def resize_image(self):
        image_width, image_height = self.source_image.size
        width_ratio = self.width / image_width
        height_ratio = self.height / image_height
        self.ratio = min(width_ratio, height_ratio)

        new_width = int(image_width * self.ratio)
        new_height = int(image_height * self.ratio)
        scaled_image = self.source_image.resize((new_width, new_height))
        self.image = ImageTk.PhotoImage(scaled_image)

    def paste_image(self):
        self.image_id = self.create_image(
            self.center_x, self.center_y, image=self.image)

    def open_image(self, filename: str, annotations: List[Model.Image.Annotation]):
        self.selected_annotation_idx = -1
        self.is_resizing = False
        self.delete_previous_image()
        self.source_image = PIL.Image.open(filename)
        self.image = ImageTk.PhotoImage(self.source_image)
        self.annotations = annotations
        if len(self.annotations) > 0:
            self.selected_annotation_idx = 0
        self.resize_image()
        self.paste_image()
        self.draw_annotations()

    def draw_annotations(self):
        for r_id in self.rect_ids:
            self.delete(r_id)
        for t_id in self.text_ids:
            self.delete(t_id)

        for h_id in self.handle_ids:
            self.delete(h_id)

        self.rect_ids = []
        self.text_ids = []
        self.handle_ids = []
        for a_id, annotation in enumerate(self.annotations):
            x = annotation.x
            y = annotation.y
            color = "lightblue"
            if a_id == self.selected_annotation_idx:
                color = "blue"
            self.rect_ids.append(self.create_rectangle(x*self.ratio, y*self.ratio, (x+annotation.width)*self.ratio,
                                                       (y+annotation.height)*self.ratio, outline=color, width=3))
            self.text_ids.append(self.create_text((x+50)*self.ratio, y*self.ratio,
                                                  text=f"{annotation.label}-{a_id}", fill='red'))
            h_x = (x + annotation.width)*self.ratio
            h_y = (y + annotation.height)*self.ratio
            h_size = HANDLE_SIZE/2
            self.handle_ids.append(self.create_rectangle(
                h_x-h_size, h_y-h_size, h_x+h_size, h_y+h_size, fill="red"))


class AnnotationsInspector(tk.Frame):
    def __init__(self, inspector: InspectorInterface, master: tk.Tk, **kwargs):
        super().__init__(master, **kwargs)
        self.inspector = inspector
        self.current_image: Optional[Model.Image] = None
        self.current_annotation_index = -1
        btton = tk.Button(self, text="add", command=self.add_new)

        btton.grid(row=0, column=0)
        self.listbox = tk.Listbox(
            self, selectmode=tk.SINGLE, exportselection=False)
        self.listbox.grid(row=1, column=1)
        self.listbox.bind("<<ListboxSelect>>", self.selection_changed)

        tk.Label(self, text="x: ").grid(row=2, column=0)
        self.x_val = tk.IntVar(value=0)
        tk.Spinbox(self, textvariable=self.x_val, from_=0, to=2000,
                   increment=1).grid(row=2, column=1)

        tk.Label(self, text="y: ").grid(row=3, column=0)
        self.y_val = tk.IntVar(value=0)
        tk.Spinbox(self, textvariable=self.y_val, from_=0, to=2000,
                   increment=1).grid(row=3, column=1)

        tk.Label(self, text="w: ").grid(row=4, column=0)
        self.w_val = tk.IntVar(value=0)
        tk.Spinbox(self, textvariable=self.w_val, from_=0, to=2000,
                   increment=1).grid(row=4, column=1)

        tk.Label(self, text="h: ").grid(row=5, column=0)
        self.h_val = tk.IntVar(value=0)
        tk.Spinbox(self, textvariable=self.h_val, from_=0, to=2000,
                   increment=1).grid(row=5, column=1)

        tk.Label(self, text="label: ").grid(row=6, column=0)
        self.lbl_val = tk.StringVar(value="Label")
        self.label_entry = tk.Entry(self, textvariable=self.lbl_val, )
        self.label_entry.grid(row=6, column=1)
        self.label_entry.bind("<Return>", self.update_label)

        del_btton = tk.Button(self, text="remove", command=self.remove_anno)
        del_btton.grid(row=7, column=1)

    def remove_anno(self, _=None):
        print(f"remove annotation {self.current_annotation_index}")
        del self.current_image.annotations[self.current_annotation_index]
        if self.current_annotation_index >= 1:
            self.current_annotation_index -= 1
        if len(self.current_image.annotations) == 0:
            self.current_annotation_index = -1
        self.update_inspector(self.current_image)

    def update_label(self, _=None):
        self.current_image.annotations[self.current_annotation_index].label = self.lbl_val.get(
        )
        self.update_annotation_list()

    def update_annotation_list(self):
        self.listbox.delete(0, tk.END)
        for i, anno in enumerate(self.current_image.annotations):
            self.listbox.insert(i, f"{anno.label}-{i}")

    def update_inspector(self, image: Model.Image):
        self.current_image = image
        self.update_annotation_list()
        if len(self.current_image.annotations) > 0:
            self.do_select_annotation(0)

    def selection_changed(self, _=None):
        sel_index = self.listbox.curselection()[0]
        self.update_annotation(sel_index)

    def do_select_annotation(self, index: int):
        self.listbox.select_clear(0, tk.END)
        self.current_annotation_index = index
        self.listbox.select_set(index)
        self.update_annotation(index)

    def update_annotation(self, index: int):
        self.x_val.set(self.current_image.annotations[index].x)
        self.y_val.set(self.current_image.annotations[index].y)
        self.w_val.set(self.current_image.annotations[index].width)
        self.h_val.set(self.current_image.annotations[index].height)
        self.lbl_val.set(self.current_image.annotations[index].label)

    def add_new(self):
        self.current_image.annotations.append(Model.Image.Annotation())
        self.update_annotation_list()
        self.inspector.annotations_changed(
            len(self.current_image.annotations)-1)


class Window(tk.Tk):
    def __init__(self, project: Project, **kwargs):
        super().__init__(**kwargs)
        self.project = project
        self.title(f"Model Annotator file {self.project.folder}")
        self._setup_ui()
        self._setup_menu_bar()

    def _setup_menu_bar(self):
        menu_bar = tk.Menu(self)

        menu_file = tk.Menu(menu_bar, tearoff=0)
        menu_file.add_command(
            label="Save", command=self.save, accelerator="Command+s")
        self.bind_all("<Command-s>", self.save)
        menu_bar.add_cascade(label="File", menu=menu_file)
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
        center_widget = tk.Frame(center, bg='yellow', width=250,
                                 height=190, padx=3, pady=3)
        self.right_panel = AnnotationsInspector(self, center, bg='green', width=100,
                                                height=190, padx=3, pady=3)

        self.left_panel.grid(row=0, column=0, sticky="ns")
        center_widget.grid(row=0, column=1, sticky="nsew")
        self.right_panel.grid(row=0, column=2, sticky="ns")

        self.canvas = CanvasImage(self, center_widget, bd=2)
        self.canvas.pack(expand=True, fill='both', padx=10, pady=10)
        self.listbox = tk.Listbox(
            self.left_panel, selectmode=tk.SINGLE, exportselection=False)
        self.listbox.bind("<<ListboxSelect>>", self.img_selection_changed)
        self.listbox.pack(expand=True, fill='y')
        for i, img in enumerate(self.project.model.images):
            self.listbox.insert(i, img.filename)

    def img_selection_changed(self, _):
        sel_index = self.listbox.curselection()[0]
        img_path = self.project.get_image_path(sel_index)
        self.canvas.open_image(
            img_path, self.project.model.images[sel_index].annotations)
        self.right_panel.update_inspector(self.project.model.images[sel_index])

    def annotations_selection_changed(self, index):
        self.right_panel.do_select_annotation(index)

    def annotations_changed(self, index):
        self.right_panel.update_annotation(index)

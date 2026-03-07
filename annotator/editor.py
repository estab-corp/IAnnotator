import tkinter as tk
from typing import List, Optional, Tuple
import PIL.Image
from PIL import ImageTk
from project import Project
from model import Model
HANDLE_SIZE = 10


class InspectorInterface:
    def annotations_selection_changed(self, index):
        pass

    def annotations_changed(self, index):
        pass

    def mouse_pos_changed(self, coords: Tuple[int, int]):
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
        self.bind('<B1-Motion>', self.on_mouse_drag)
        self.bind('<Motion>', self.on_mouse_move)

    def coords_view_to_img(self, coords) -> Tuple[float, float]:
        x = self.canvasx(coords[0])
        x /= self.ratio
        x = max(x, 0)
        x = min(x, self.source_image.size[0])
        y = self.canvasx(coords[1])
        y /= self.ratio
        y = max(y, 0)
        y = min(y, self.source_image.size[1])
        return (round(x, 2), round(y, 2))

    def coords_img_to_view(self, coords) -> Tuple[float, float]:
        return (coords[0]*self.ratio, coords[1]*self.ratio)

    def on_mouse_move(self, event):
        if self.source_image is None:
            return
        coords_in_img = self.coords_view_to_img((event.x, event.y))
        self.inspector.mouse_pos_changed(coords_in_img)

    def on_mouse_drag(self, event):
        if self.source_image is None:
            return
        coords_in_img = self.coords_view_to_img((event.x, event.y))
        self.inspector.mouse_pos_changed(coords_in_img)
        if self.selected_annotation_idx < 0:
            return
        annotation = self.annotations[self.selected_annotation_idx]
        if self.is_resizing:
            annotation.width = round(coords_in_img[0]-annotation.x, 2)
            annotation.height = round(coords_in_img[1]-annotation.y, 2)
        else:
            annotation.x = round(
                coords_in_img[0] - self.move_origin_offset[0], 2)
            annotation.y = round(
                coords_in_img[1] - self.move_origin_offset[1], 2)

        self.inspector.annotations_changed(self.selected_annotation_idx)
        self.draw_annotations()

    def on_click(self, event):
        self.selected_annotation_idx = -1
        for a_id, annotation in enumerate(self.annotations):
            x, y = self.coords_img_to_view((annotation.x, annotation.y))
            w, h = self.coords_img_to_view(
                (annotation.width, annotation.height))

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
                img_event_coords = self.coords_view_to_img((event.x, event.y))
                self.move_origin_offset = (
                    img_event_coords[0] - annotation.x, img_event_coords[1] - annotation.y)
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
        self.render_image()
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

    def render_image(self):
        self.image_id = self.create_image(0, 0, anchor="nw", image=self.image)

    def open_image(self, filename: str, annotations: List[Model.Image.Annotation]) -> Tuple[int, int]:
        self.selected_annotation_idx = -1
        self.is_resizing = False
        self.delete_previous_image()
        self.source_image = PIL.Image.open(filename)
        self.image = ImageTk.PhotoImage(self.source_image)
        self.annotations = annotations
        if len(self.annotations) > 0:
            self.selected_annotation_idx = 0
        self.resize_image()
        self.render_image()
        self.draw_annotations()
        return self.source_image.size

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
            r_x0, r_y0 = self.coords_img_to_view((x, y))
            r_x1, r_y1 = self.coords_img_to_view(
                (x+annotation.width, y+annotation.height))
            self.rect_ids.append(self.create_rectangle(
                r_x0, r_y0, r_x1, r_y1, outline=color, width=3))
            self.text_ids.append(self.create_text(r_x0+40, r_y0,
                                                  text=f"{annotation.label}-{a_id}", fill='red'))

            h_size = HANDLE_SIZE/2
            self.handle_ids.append(self.create_rectangle(
                r_x1-h_size, r_y1-h_size, r_x1+h_size, r_y1+h_size, fill="red"))


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
        self.listbox = tk.Listbox(
            self.annotations_frame, selectmode=tk.SINGLE, exportselection=False)
        self.listbox.grid(row=1, column=1)
        self.listbox.bind("<<ListboxSelect>>", self.selection_changed)

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
        self.listbox.delete(0, tk.END)
        for i, anno in enumerate(self.current_image.annotations):
            self.listbox.insert(i, f"{anno.label}-{i}")
        if len(self.current_image.annotations) > 0:
            self.do_select_annotation(0)

    def update_inspector(self, image: Model.Image, img_w: int, img_h: int):
        self.current_image = image
        self.img_size_val.set(f"w={img_w} h={img_h}")
        self.update_annotation_list()

    def selection_changed(self, _=None):
        sel_index = self.listbox.curselection()[0]
        self.update_annotation(sel_index)

    def do_select_annotation(self, index: int):
        self.listbox.select_clear(0, tk.END)
        self.current_annotation_index = index
        self.listbox.select_set(index)
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


class AnnotatorWindow(tk.Tk):
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
        self.right_panel = AnnotationsInspector(self, center, bg='green', width=100,
                                                height=190, padx=3, pady=3)

        self.left_panel.grid(row=0, column=0, sticky="ns")
        self.right_panel.grid(row=0, column=2, sticky="ns")

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
        img_w, img_h = self.canvas.open_image(
            img_path, self.project.model.images[sel_index].annotations)
        self.right_panel.update_inspector(
            self.project.model.images[sel_index], img_w, img_h)

    def annotations_selection_changed(self, index):
        self.right_panel.do_select_annotation(index)

    def annotations_changed(self, index):
        self.right_panel.update_annotation(index)
        self.canvas.draw_annotations()

    def mouse_pos_changed(self, coords: Tuple[int, int]):
        self.right_panel.mouse_pos_changed(coords)

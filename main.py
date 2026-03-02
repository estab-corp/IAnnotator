import PIL.Image
import tkinter as tk
from PIL import ImageTk
import json
import argparse
from typing import List, Optional
import os


parser = argparse.ArgumentParser(prog='IAnnotator')
parser.add_argument('jsonfile', metavar="JSON file")


class Project:
    class Image:
        class Annotation:
            def __init__(self):
                self.label: str = "LABEL"
                self.width = 100
                self.height = 200
                self.x = 300
                self.y = 400

            def from_data(self, data: dict):
                self.label: str = data["label"]
                center_x = data["coordinates"]["x"]
                center_y = data["coordinates"]["y"]
                self.width = data["coordinates"]["width"]
                self.height = data["coordinates"]["height"]
                self.x = center_x - self.width/2
                self.y = center_y - self.height/2

            def save(self) -> dict:
                center_x = self.x + self.width/2
                center_y = self.y + self.height/2
                ret = {
                    "label": self.label,
                    "coordinates": {
                        "x": center_x,
                        "y": center_y,
                        "width": self.width,
                        "height": self.height,
                    }
                }
                return ret

        def __init__(self):
            self.annotations: List[Project.Image.Annotation] = []
            self.filename: str = ""

        def from_data(self, data: dict):
            self.filename: str = data["imagefilename"]
            for entry in data["annotations"]:
                annotation = Project.Image.Annotation()
                annotation.from_data(entry)
                self.annotations.append(annotation)

        def save(self) -> dict:
            annotations = []
            for annotation in self.annotations:
                annotations.append(annotation.save())
            ret = {
                "imagefilename": self.filename,
                "annotations": annotations
            }
            return ret

    def __init__(self, data: dict, folder: str, json_file: str):
        self.json_file = json_file
        self.folder = folder
        self.images: List[Project.Image] = []
        self._load(data)

    def _load(self, data: dict):
        for entry in data:
            img = Project.Image()
            img.from_data(entry)
            self.images.append(img)

    def get_image_path(self, index: int):
        return self.folder + "/" + self.images[index].filename

    def save(self) -> List:
        ret = []
        for img in self.images:
            ret.append(img.save())
        return ret

    def save_file(self):
        data = self.save()
        with open(self.json_file, "w", encoding="utf-8") as f:
            json.dump(data, f)


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
        self.annotations: List[Project.Image.Annotation] = []
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

    def open_image(self, filename: str, annotations: List[Project.Image.Annotation]):
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
    def __init__(self, master: tk.Tk, **kwargs):
        super().__init__(master, **kwargs)
        self.current_image: Optional[Project.Image] = None
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

    def update_inspector(self, image: Project.Image):
        self.current_image = image
        self.listbox.delete(0, tk.END)
        for i, anno in enumerate(image.annotations):
            self.listbox.insert(i, f"{anno.label}-{i}")
        self.do_select_annotation(0)

    def selection_changed(self, _=None):
        sel_index = self.listbox.curselection()[0]
        self.update_annotation(sel_index)

    def do_select_annotation(self, index: int):
        self.listbox.select_clear(0, tk.END)
        self.listbox.select_set(index)
        self.update_annotation(index)

    def update_annotation(self, index: int):
        self.x_val.set(self.current_image.annotations[index].x)
        self.y_val.set(self.current_image.annotations[index].y)
        self.w_val.set(self.current_image.annotations[index].width)
        self.h_val.set(self.current_image.annotations[index].height)

    def add_new(self):
        self.current_image.annotations.append(Project.Image.Annotation())


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
        self.right_panel = AnnotationsInspector(center, bg='green', width=100,
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
        for i, img in enumerate(self.project.images):
            self.listbox.insert(i, img.filename)

    def img_selection_changed(self, _):
        sel_index = self.listbox.curselection()[0]
        img_path = self.project.get_image_path(sel_index)
        self.canvas.open_image(
            img_path, self.project.images[sel_index].annotations)
        self.right_panel.update_inspector(self.project.images[sel_index])

    def annotations_selection_changed(self, index):
        self.right_panel.do_select_annotation(index)

    def annotations_changed(self, index):
        self.right_panel.update_annotation(index)


if __name__ == '__main__':
    args = parser.parse_args()
    json_file = args.jsonfile
    with open(json_file, encoding="utf-8") as f:
        data = json.load(f)
        folder = os.path.dirname(json_file)
        project = Project(data, folder, json_file)
        window = Window(project)
        window.mainloop()

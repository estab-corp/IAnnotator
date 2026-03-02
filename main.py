import PIL.Image
import tkinter as tk
from PIL import ImageTk
from tkinter.filedialog import askopenfilename
import json
import argparse
from typing import List
import os


parser = argparse.ArgumentParser(prog='IAnnotator')
parser.add_argument('jsonfile', metavar="JSON file")


class Project:
    class Image:
        class Annotation:
            def __init__(self, data: dict):
                self.label: str = data["label"]
                self.center_x = data["coordinates"]["x"]
                self.center_y = data["coordinates"]["y"]
                self.width = data["coordinates"]["width"]
                self.height = data["coordinates"]["height"]

            def print(self):
                print(
                    f"\tlabel={self.label} x={self.center_x} y={self.center_y} w={self.width} h={self.height}")

        def __init__(self, data: dict):
            self.annotations: List[Project.Image.Annotation] = []
            self.filename: str = data["imagefilename"]
            for entry in data["annotations"]:
                self.annotations.append(Project.Image.Annotation(entry))

        def print(self):
            print(f"filename: {self.filename}")
            for annotation in self.annotations:
                annotation.print()

    def __init__(self, data: dict, folder: str):
        self.folder = folder
        self.images: List[Project.Image] = []
        self._load(data)

    def _load(self, data: dict):
        for entry in data:
            self.images.append(Project.Image(entry))

    def get_image_path(self, index: int):
        return self.folder + "/" + self.images[index].filename

    def print(self):
        for img in self.images:
            img.print()


class CanvasImage(tk.Canvas):
    def __init__(self, master: tk.Tk, **kwargs):
        super().__init__(master, **kwargs)
        self.ratio = 1
        self.source_image = None
        self.image_id = None
        self.image = None
        self.selected_annotation_idx = -1

        self.annotations: List[Project.Image.Annotation] = []
        self.rect_ids = []
        self.text_ids = []
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
        annotation.center_x = real_x
        annotation.center_y = real_y
        self.draw_annotations()

    def on_click(self, event):
        self.selected_annotation_idx = -1
        for a_id, annotation in enumerate(self.annotations):
            x = (annotation.center_x - (annotation.width/2))*self.ratio
            y = (annotation.center_y - (annotation.height/2))*self.ratio
            w = annotation.width*self.ratio
            h = annotation.height*self.ratio
            if x <= event.x <= x+w and y <= event.y <= y+h:
                print(f"Clicked {annotation.label} {a_id}")
                self.selected_annotation_idx = a_id
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
        self.delete_previous_image()
        self.source_image = PIL.Image.open(filename)
        self.image = ImageTk.PhotoImage(self.source_image)
        self.annotations = annotations
        self.resize_image()
        self.paste_image()
        self.draw_annotations()

    def draw_annotations(self):
        for r_id in self.rect_ids:
            self.delete(r_id)
        for t_id in self.text_ids:
            self.delete(t_id)
        self.rect_ids = []
        self.text_ids = []
        for annotation in self.annotations:
            x = annotation.center_x - (annotation.width/2)
            y = annotation.center_y - (annotation.height/2)
            self.rect_ids.append(self.create_rectangle(x*self.ratio, y*self.ratio, (x+annotation.width)*self.ratio,
                                                       (y+annotation.height)*self.ratio, outline="blue", width=3))
            self.text_ids.append(self.create_text((x+50)*self.ratio, y*self.ratio,
                                                  text=annotation.label, fill='red'))


class Window(tk.Tk):
    def __init__(self, project: Project, **kwargs):
        super().__init__(**kwargs)
        self.project = project
        self.title(f"Model Annotator file {self.project.folder}")
        self._setup_ui()

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
        right_panel = tk.Frame(center, bg='green', width=100,
                               height=190, padx=3, pady=3)

        self.left_panel.grid(row=0, column=0, sticky="ns")
        center_widget.grid(row=0, column=1, sticky="nsew")
        right_panel.grid(row=0, column=2, sticky="ns")

        self.canvas = CanvasImage(center_widget, bd=2)
        self.canvas.pack(expand=True, fill='both', padx=10, pady=10)
        self.listbox = tk.Listbox(self.left_panel, selectmode=tk.SINGLE)
        self.listbox.bind("<<ListboxSelect>>", self.img_selection_changed)
        self.listbox.pack(expand=True, fill='y')
        for i, img in enumerate(self.project.images):
            self.listbox.insert(i, img.filename)

    def img_selection_changed(self, _):
        sel_index = self.listbox.curselection()[0]
        img_path = self.project.get_image_path(sel_index)
        print(f"selected index = {sel_index} path='{img_path}'")
        self.canvas.open_image(
            img_path, self.project.images[sel_index].annotations)


if __name__ == '__main__':
    args = parser.parse_args()
    json_file = args.jsonfile
    with open(json_file) as f:
        data = json.load(f)
        folder = os.path.dirname(json_file)
        project = Project(data, folder)
        # project.print()
        window = Window(project)
        window.mainloop()

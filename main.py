import PIL.Image
import tkinter as tk
from PIL import ImageTk
from tkinter.filedialog import askopenfilename
import json
import argparse
from typing import List


parser = argparse.ArgumentParser(prog='IAnnotator')
parser.add_argument('jsonfile', metavar="JSON file")


class Project:
    class Image:
        class Annotation:
            def __init__(self, data: dict):
                self.label: str = data["label"]
                self.x = data["coordinates"]["x"]
                self.y = data["coordinates"]["y"]
                self.width = data["coordinates"]["width"]
                self.height = data["coordinates"]["height"]

            def print(self):
                print(
                    f"\tlabel={self.label} x={self.x} y={self.y} w={self.width} h={self.height}")

        def __init__(self, data: dict):
            self.annotations: List[Project.Image.Annotation] = []
            self.filename: str = data["imagefilename"]
            for entry in data["annotations"]:
                self.annotations.append(Project.Image.Annotation(entry))

        def print(self):
            print(f"filename: {self.filename}")
            for annotation in self.annotations:
                annotation.print()

    def __init__(self, data: dict):
        self.images: List[Project.Image] = []
        self._load(data)

    def _load(self, data: dict):
        for entry in data:
            self.images.append(Project.Image(entry))

    def print(self):
        for img in self.images:
            img.print()


class CanvasImage(tk.Canvas):
    def __init__(self, master: tk.Tk, **kwargs):
        super().__init__(master, **kwargs)

        self.source_image = None
        self.image_id = None
        self.image = None

        self.width, self.height = 0, 0
        self.center_x, self.center_y = 0, 0
        self.bind('<Configure>', self.update_values)

    def update_values(self, *_) -> None:
        self.width = self.winfo_width()
        self.height = self.winfo_height()
        self.center_x = self.width//2
        self.center_y = self.height//2

        if self.image is None:
            return
        self.delete_previous_image()
        self.resize_image()
        self.paste_image()

    def delete_previous_image(self) -> None:
        if self.image is None:
            return
        self.delete(self.image_id)
        self.image = self.image_id = None

    def resize_image(self) -> None:
        image_width, image_height = self.source_image.size
        width_ratio = self.width / image_width
        height_ratio = self.height / image_height
        ratio = min(width_ratio, height_ratio)

        new_width = int(image_width * ratio)
        new_height = int(image_height * ratio)
        scaled_image = self.source_image.resize((new_width, new_height))
        self.image = ImageTk.PhotoImage(scaled_image)

    def paste_image(self) -> None:
        self.image_id = self.create_image(
            self.center_x, self.center_y, image=self.image)

    def open_image(self) -> None:
        if not (filename := askopenfilename()):
            return

        self.delete_previous_image()
        self.source_image = PIL.Image.open(filename)
        self.image = ImageTk.PhotoImage(self.source_image)

        self.resize_image()
        self.paste_image()


class Window(tk.Tk):
    def __init__(self, project: Project, **kwargs):
        super().__init__(**kwargs)
        self.project = project
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
        tk.Button(center_widget, text='Open',
                  comman=self.canvas.open_image).pack()
        self.canvas.pack(expand=True, fill='both', padx=10, pady=10)
        self._setup_left_panel()

    def _setup_left_panel(self):
        listbox = tk.Listbox(self.left_panel)
        listbox.pack()
        for i, img in enumerate(self.project.images):
            listbox.insert(i, img.filename)


if __name__ == '__main__':
    args = parser.parse_args()
    json_file = args.jsonfile
    with open(json_file) as f:
        data = json.load(f)
        project = Project(data)
        # project.print()
        window = Window(project)
        window.mainloop()

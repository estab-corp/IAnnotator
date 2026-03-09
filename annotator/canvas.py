import tkinter as tk
from typing import List, Tuple
import PIL.Image
from PIL import ImageTk
from model import Model
from annotator.inspector_interface import InspectorInterface

HANDLE_SIZE = 10


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
        self.is_dragging = False
        self.bind('<Configure>', self.update_values)
        self.bind('<ButtonPress-1>', self.on_click)
        self.bind('<ButtonRelease-1>', self.on_release)
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
        self.draw_rulers((event.x, event.y))

    def on_mouse_drag(self, event):
        self.is_dragging = True
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
        self.draw_rulers((event.x, event.y))

    def on_release(self, _):
        if self.is_dragging:
            print("Was dragging")
        self.is_dragging = False

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

    def draw_rulers(self, mouse_pos):
        self.delete("rulers")
        color = "red"
        self.create_line(mouse_pos[0], 0, mouse_pos[0],
                         self.height, dash=(5, 5), fill=color, tags="rulers")
        self.create_line(0, mouse_pos[1], self.width,
                         mouse_pos[1], dash=(5, 5), fill=color, tags="rulers")

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

import tkinter as tk
from typing import Tuple, Optional, Set
import PIL.Image
from PIL import ImageTk
from project.project import Project
from project.cmd_manager import ChangeReason, ChangeDiff
from abc import ABC, abstractmethod


HANDLE_SIZE = 10


class CanvasWatcher(ABC):
    @abstractmethod
    def mouse_pos_changed(self, coords: Tuple[int, int]):
        pass

    @abstractmethod
    def annotation_is_changing(self, img_idx: int, anno_indices: Set[int]):
        pass

    @abstractmethod
    def canvas_selection_changed(self, anno_indices: Set[int]):
        pass


class CanvasImage(tk.Canvas):
    def __init__(self, project: Project, watcher: CanvasWatcher, master: tk.Tk, **kwargs):
        super().__init__(master, **kwargs)
        self.project = project
        self.watcher = watcher
        self.ratio = 1
        self.source_image: Optional[PIL.Image.Image] = None
        self.img_load_error = False
        self.image_id = None
        self.image = None
        self.selected_annotation_idx = -1
        self.img_idx = -1
        self.move_origin_offset_screen = (0, 0)
        self.move_origin_offset_img = (0, 0)
        # this stores the starting drag  X position in image coords
        self.start_move_x = 0
        # this stores the starting drag Y position in image coords
        self.start_move_y = 0
        # when resizing, this will store original width
        self.start_move_w = 0
        # when resizing, this will store original height
        self.start_move_h = 0
        self.is_resizing = False
        self.selection_area: Optional[Tuple[int, int]] = None
        self._move_moved_at_least_once_in_selection = False
        self.rect_ids = []
        self.text_ids = []
        self.handle_ids = []
        self.width, self.height = 0, 0
        self.center_x, self.center_y = 0, 0
        self.is_dragging = False
        self.bind('<Configure>', self._update_values)
        self.bind('<ButtonPress-1>', self.on_mouse_click)
        self.bind('<ButtonRelease-1>', self.on_mouse_release)
        self.bind('<B1-Motion>', self.on_mouse_drag)
        self.bind('<Motion>', self.on_mouse_move)

    def reset(self):
        self.clear_annotations()
        self.img_load_error = False
        self.selected_annotation_idx = -1
        self.is_resizing = False
        self.selection_area = None
        self._move_moved_at_least_once_in_selection = False
        self._delete_previous_image()

    def coords_view_to_img(self, coords) -> Tuple[float, float]:
        assert self.source_image
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
        self.watcher.mouse_pos_changed(coords_in_img)
        self.draw_rulers((event.x, event.y))

    def _calc_new_rect(self, coords_in_img):
        mdl_img = self.project.model.images[self.img_idx]
        assert mdl_img
        annotation = mdl_img.annotations[self.selected_annotation_idx]
        if self.is_resizing:
            annotation.width = round(coords_in_img[0]-annotation.x, 2)
            annotation.height = round(coords_in_img[1]-annotation.y, 2)
        else:
            annotation.x = round(
                coords_in_img[0] - self.move_origin_offset_img[0], 2)
            annotation.y = round(
                coords_in_img[1] - self.move_origin_offset_img[1], 2)

    def on_mouse_drag(self, event):
        if self.selection_area is not None:
            self._move_moved_at_least_once_in_selection = True
            self.selection_area = (event.x, event.y)
            self.draw_selection_area()
            return
        self.is_dragging = True
        if self.source_image is None:
            return
        coords_in_img = self.coords_view_to_img((event.x, event.y))
        self.watcher.mouse_pos_changed(coords_in_img)
        if self.selected_annotation_idx < 0:
            return
        self._calc_new_rect(coords_in_img)
        self.draw_annotations()

        rulers_pos = (
            event.x-self.move_origin_offset_screen[0], event.y - self.move_origin_offset_screen[1])
        if self.is_resizing:
            rulers_pos = (event.x, event.y)
        self.draw_rulers(rulers_pos)
        self.watcher.annotation_is_changing(
            self.img_idx, {self.selected_annotation_idx})

    def on_mouse_release(self, event):
        mdl_img = self.project.model.images[self.img_idx]
        assert mdl_img
        if self.selection_area is not None:
            self.delete("selection")
            if self._move_moved_at_least_once_in_selection:
                self.update_selection()
            self.selection_area = None
            self._move_moved_at_least_once_in_selection = False
            return
        if not self.is_dragging or self.selected_annotation_idx == -1:
            return
        self.is_dragging = False
        coords_in_img = self.coords_view_to_img((event.x, event.y))
        self._calc_new_rect(coords_in_img)

        annotation = mdl_img.annotations[self.selected_annotation_idx]
        diff = ChangeDiff()
        diff.x = annotation.x - self.start_move_x
        diff.y = annotation.y - self.start_move_y
        diff.w = annotation.width - self.start_move_w
        diff.h = annotation.height - self.start_move_h
        self.project.update_annotation(
            img_idx=self.img_idx, anno_idx=self.selected_annotation_idx, diff=diff, reason=ChangeReason.ANNO_GEOMETRY)

    def on_mouse_click(self, event):
        if self.source_image is None:
            return
        mdl_img = self.project.model.images[self.img_idx]
        assert mdl_img
        prev_selected_annotation_idx = self.selected_annotation_idx
        self.selected_annotation_idx = -1
        img_event_coords = self.coords_view_to_img((event.x, event.y))
        for a_id, annotation in enumerate(mdl_img.annotations):
            x, y = self.coords_img_to_view((annotation.x, annotation.y))
            w, h = self.coords_img_to_view(
                (annotation.width, annotation.height))

            h_x = x+w
            h_y = y+h
            h_size = HANDLE_SIZE/2
            if h_x-h_size <= event.x <= h_x+h_size and h_y-h_size <= event.y <= h_y+h_size:
                self.selected_annotation_idx = a_id
                self.is_resizing = True
                self.start_move_x = annotation.x
                self.start_move_y = annotation.y
                break
            if x <= event.x <= x+w and y <= event.y <= y+h:
                self.selected_annotation_idx = a_id
                self.is_resizing = False

                self.move_origin_offset_screen = (event.x-x, event.y-y)
                self.move_origin_offset_img = (
                    img_event_coords[0] - annotation.x, img_event_coords[1] - annotation.y)
                self.start_move_x = round(
                    img_event_coords[0] - self.move_origin_offset_img[0], 2)
                self.start_move_y = round(
                    img_event_coords[1] - self.move_origin_offset_img[1], 2)
                break
        if self.selected_annotation_idx == -1:
            assert self.selection_area is None
            self.selection_area = (0, 0)
            self.move_origin_offset_screen = (event.x, event.y)
            return
        if prev_selected_annotation_idx != self.selected_annotation_idx:
            self.watcher.canvas_selection_changed(
                {self.selected_annotation_idx})
        annotation = mdl_img.annotations[self.selected_annotation_idx]
        self.start_move_w = annotation.width
        self.start_move_h = annotation.height
        self.draw_annotations()

    def _update_values(self, *_):
        self.width = self.winfo_width()
        self.height = self.winfo_height()
        self.center_x = self.width//2
        self.center_y = self.height//2

        if self.image is None:
            return
        self._delete_previous_image()
        self.resize_image()
        self.render_image()
        self.draw_annotations()

    def _delete_previous_image(self):
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

    def show_image(self, filename: str, img_idx: int) -> bool:
        image = self.project.model.images[img_idx]
        self.img_idx = img_idx
        self.selected_annotation_idx = -1
        self.is_resizing = False
        self._delete_previous_image()
        try:
            self.source_image = PIL.Image.open(filename)
        except FileNotFoundError as e:
            r_x0, r_y0 = self.coords_img_to_view((500, 500))
            self.clear_annotations()
            self.text_ids.append(self.create_text(
                r_x0, r_y0, text=f"error {e}", fill='red'))
            self.img_load_error = True
            return False
        self.img_load_error = False
        assert self.source_image
        self.image = ImageTk.PhotoImage(self.source_image)
        self.resize_image()
        self.render_image()
        self.draw_annotations()
        image.loaded_width = self.source_image.size[0]
        image.loaded_height = self.source_image.size[1]
        return True

    def update_selection(self):
        assert self.selection_area
        b_x0, b_y0 = self.coords_view_to_img(self.move_origin_offset_screen)
        b_x1, b_y1 = self.coords_view_to_img(self.selection_area)
        if b_x1 < b_x0:
            b_x0, b_x1 = b_x1, b_x0
        if b_y1 < b_y0:
            b_y0, b_y1 = b_y1, b_y0

        mdl_img = self.project.model.images[self.img_idx]
        selected = []
        for a_id, annotation in enumerate(mdl_img.annotations):
            x = annotation.x
            y = annotation.y
            w = annotation.width
            h = annotation.height
            if b_x0 <= x <= b_x1 and x+w < b_x1:
                if b_y0 <= y <= b_y1 and y+h < b_y1:
                    selected.append(a_id)
        print(selected)

    def draw_selection_area(self):
        assert self.selection_area
        self.delete("selection")
        color = "red"
        self.create_rectangle(
            self.move_origin_offset_screen[0],
            self.move_origin_offset_screen[1],
            self.selection_area[0],
            self.selection_area[1],
            outline=color,
            tags="selection")

    def draw_rulers(self, mouse_pos):
        self.delete("rulers")
        color = "red"
        self.create_line(mouse_pos[0], 0, mouse_pos[0],
                         self.height, dash=(5, 5), fill=color, tags="rulers")
        self.create_line(0, mouse_pos[1], self.width,
                         mouse_pos[1], dash=(5, 5), fill=color, tags="rulers")

    def clear_annotations(self):
        for r_id in self.rect_ids:
            self.delete(r_id)
        for t_id in self.text_ids:
            self.delete(t_id)

        for h_id in self.handle_ids:
            self.delete(h_id)

    def select_annotation(self, anno_index: int):
        if self.img_load_error:
            return
        self.selected_annotation_idx = anno_index
        self.draw_annotations()

    def draw_annotations(self):
        self.clear_annotations()
        mdl_img = self.project.model.images[self.img_idx]
        assert mdl_img

        self.rect_ids = []
        self.text_ids = []
        self.handle_ids = []
        for a_id, annotation in enumerate(mdl_img.annotations):
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

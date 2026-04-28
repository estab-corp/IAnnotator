import tkinter as tk
from tkinter import ttk
from typing import Tuple, List, Dict
import bisect
from project.model import Model


def _find_closest_index(lst: List[int], val: int):
    i = bisect.bisect_left(lst, val)
    if i >= len(lst):
        i = len(lst) - 1
    elif i and lst[i] - val > val - lst[i - 1]:
        i = i - 1
    return i


def _get_index_from_image_iid(item_iid: str):
    assert item_iid.startswith("I")
    return int(item_iid[1:])


class ImageTreeWidget(ttk.Treeview):
    def __init__(self, parent):
        super().__init__(parent)
        self.invalid_tag = self.tag_configure("error", foreground="red")

    def reset(self):
        self.delete(*self.get_children())

    def select_image_index(self, img_index: int):
        cur_img_index, _ = self.get_selected_tuple()
        if cur_img_index == img_index:
            return
        self.selection_set(f"I{img_index}")

    def mark_invalid_img(self, img_index: int):
        img_item_index = f"I{img_index}"
        self.item(img_item_index, tags="error")

    def update_selected_annotation(self, anno_index: int):
        img_index, cur_anno_index = self.get_selected_tuple()
        if anno_index == cur_anno_index:
            return
        new_id = f"A{anno_index}:I{img_index}"
        self.selection_set(new_id)

    def get_selected_tuple(self) -> Tuple[int, int]:
        if len(self.selection()) == 0:
            return (-1, -1)
        item_iid: str = self.selection()[0]
        parent_iid: str = self.parent(item_iid)
        if parent_iid == "":
            return (_get_index_from_image_iid(item_iid), -1)
        sel_image = _get_index_from_image_iid(parent_iid)
        assert item_iid.startswith("A")  # this is an annotation
        sel_anno = int(item_iid[1:].split(":")[0])
        return (sel_image, sel_anno)

    def _select_closest_img_anno(self, sel_img: int, sel_anno: int):
        if sel_img == -1:
            return
        # if sel_anno has disappeared, likely due to being removed,
        # we try and get the previous annotation index. If no lower index, selected the parent image
        img_item_index = f"I{sel_img}"
        self.item(img_item_index, open=True)
        anno_items = self.get_children(img_item_index)

        item_to_select = ""
        if len(anno_items) == 0:
            item_to_select = img_item_index
        else:
            indexes: List[int] = []
            for item in anno_items:
                anno_idx = int(item[1:].split(":")[0])
                indexes.append(anno_idx)
            indexes = sorted(indexes)  # not sure if indexes are sorted
            next_sel_anno = _find_closest_index(indexes, sel_anno)
            item_to_select = f"A{next_sel_anno}:"+img_item_index

        if item_to_select != "":
            self.selection_set(item_to_select)

    def _get_open_states(self) -> Dict[str, bool]:
        ret = {}
        for entry in self.get_children():
            ret[entry] = self.item(entry)["open"]
        return ret

    def update_image_list(self, model: Model):
        sel_img, sel_anno = self.get_selected_tuple()
        open_states = self._get_open_states()
        self.delete(*self.get_children())
        for i, img in enumerate(model.images):
            item = self.insert(
                "", tk.END, text=img.filename, iid=f"I{i}")
            for anno_i, anno in enumerate(img.annotations):
                self.insert(
                    item, tk.END, text=anno.label, iid=f"A{anno_i}:I{i}")
        if sel_img == -1:
            return

        for item, is_open in open_states.items():
            self.item(item, open=is_open)
        self._select_closest_img_anno(sel_img, sel_anno)

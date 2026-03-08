from typing import Tuple


class InspectorInterface:
    def annotations_selection_changed(self, index):
        pass

    def annotations_changed(self, index):
        pass

    def mouse_pos_changed(self, coords: Tuple[int, int]):
        pass

import tkinter as tk
from project.project import Project
from tkinter import ttk


def show_train_win(parent, model: Project) -> tk.Toplevel:
    new_win = TrainerTopWindow(parent, model)
    return new_win


title = "trainer"
default_geometry = ("600x600")


def _conf_trainer_win(win, project):
    win.title(f"Trainer file {project.json_file}")
    win.geometry(default_geometry)
    frame = TrainerFrame(win, project)
    frame.pack(expand=True, fill='both')
    win.bind('<<NotebookTabChanged>>',
             lambda event: win.update_idletasks())


class TrainerTopWindow(tk.Toplevel):
    def __init__(self, parent, project: Project):
        super().__init__(parent)
        _conf_trainer_win(self, project)


class TrainerWindow(tk.Tk):
    def __init__(self, project: Project):
        super().__init__()
        _conf_trainer_win(self, project)


class TrainerFrame(tk.Frame):
    def __init__(self, parent, project: Project):
        super().__init__(parent)
        self.project = project

        self.note_book = ttk.Notebook(self)
        self.note_book.pack(expand=True, fill='both')

        # setup frame
        self.setup_frame = tk.Frame(self.note_book)
        self.annotations_frame = tk.LabelFrame(
            self.setup_frame, text="training data")
        self.annotations_frame.pack()
        num_classes = len(self.project.model.get_classes())
        num_classes_label = tk.Label(
            self.annotations_frame, text=f"{num_classes} Class{"es" if num_classes > 1 else ""}")
        num_classes_label.grid(row=0, column=0)

        num_items = self.project.model.get_num_annotations()
        num_items_label = tk.Label(
            self.annotations_frame, text=f"{num_items} Item{"s" if num_items > 1 else ""}")
        num_items_label.grid(row=0, column=1)

        self.note_book.add(self.setup_frame, text="Setup")

        # training frame
        self.training_frame = tk.Frame(self.note_book)
        self.note_book.add(self.training_frame, text="Training")

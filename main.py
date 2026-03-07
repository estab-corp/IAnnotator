import json
import argparse
import os
import sys
from typing import Optional, Tuple, IO
from annotator.editor import AnnotatorWindow
from project import Project
import formats
from model import Model

parser = argparse.ArgumentParser(prog='IAnnotator')
parser.add_argument(
    '--in-format', help="json format input. Will try all formats if omitted")
parser.add_argument('input', metavar="JSON file input file", nargs='?')
parser.add_argument('output', metavar="JSON file ouput file", nargs='?')
parser.add_argument('--convert', help="convert to a different format")
parser.add_argument('--list-formats', action="store_true",
                    help="list supported formats")
parser.add_argument('--image-path', help="use a different path for images")


def list_formats():
    for form in formats.available_formats():
        print(form)


def load_model(file: IO, in_format: Optional[str]) -> Tuple[Optional[Model], str]:
    if in_format is None:
        for form in formats.available_formats():
            file.seek(0)
            print(f"tying format {form}")
            try:
                model, _ = load_model(file, form)
                return (model, form)
            except Exception:
                pass
        raise TypeError("unable to read file")

    print(f"load document using format '{in_format}'")
    model = formats.import_from(in_format, file)
    return (model, in_format)


if __name__ == '__main__':
    args = parser.parse_args()
    if args.list_formats:
        list_formats()
        sys.exit(0)
    if args.input is None:
        print("missing input file")
        parser.print_usage()
        sys.exit(1)
    if args.convert and args.output is None:
        print("missing output file")
        parser.print_usage()
        sys.exit(1)
    json_file = args.input
    with open(json_file, encoding="utf-8") as file:
        model, fmt = load_model(file, args.in_format)
        if model is None:
            sys.exit(1)
        folder = os.path.dirname(json_file)
        if args.image_path is not None:
            folder = args.image_path
        project = Project(model)
        project.default_format = fmt
        project.folder = folder
        project.json_file = json_file

        if args.convert:
            print(
                f"write document '{args.output}' using format '{args.convert}'")

            if not formats.export_to(args.convert, model, args.output):
                print("Error")
                sys.exit(1)

        else:
            window = AnnotatorWindow(project)
            window.mainloop()

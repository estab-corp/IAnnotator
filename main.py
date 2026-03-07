import json
import argparse
import os
import sys
from typing import Optional, Tuple
from annotator.editor import Window
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


def load_model(data: any, in_format: Optional[str]) -> Tuple[Optional[Model], str]:
    if in_format is None:
        for form in formats.available_formats():
            print(f"tying format {form}")
            try:
                model, _ = load_model(data, form)
                return (model, form)
            except ValueError:
                pass

    print(f"load document using format '{in_format}'")
    model = formats.import_from(in_format, data)
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
    with open(json_file, encoding="utf-8") as f:
        data = json.load(f)
        model, format = load_model(data, args.in_format)
        if model is None:
            sys.exit(1)
        folder = os.path.dirname(json_file)
        if args.image_path is not None:
            folder = args.image_path
        project = Project(model)
        project.default_format = format
        project.folder = folder
        project.json_file = json_file

        if args.convert:
            print(
                f"write document '{args.output}' using format '{args.convert}'")
            data = formats.export_to(args.convert, model)
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(data, f)
        else:
            window = Window(project)
            window.mainloop()

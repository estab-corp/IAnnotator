import argparse
import sys
from annotator.editor import AnnotatorWindow
from project.project import Project
import formats
from project.model import Model

parser = argparse.ArgumentParser(prog='IAnnotator')
parser.add_argument(
    '--in-format', help="json format input. Will try all formats if omitted")
parser.add_argument('input', metavar="JSON file input file", nargs='?')
parser.add_argument('output', metavar="JSON file ouput file", nargs='?')
parser.add_argument('--convert', help="convert to a different format")
parser.add_argument('--list-formats', action="store_true",
                    help="list supported formats")


def list_formats():
    for form in formats.available_formats():
        print(form)


if __name__ == '__main__':
    args = parser.parse_args()
    if args.list_formats:
        list_formats()
        sys.exit(0)
    if args.input is None:
        project = Project.new_default()
        window = AnnotatorWindow(project)
        window.mainloop()
        sys.exit(1)
    if args.convert and args.output is None:
        print("missing output file")
        parser.print_usage()
        sys.exit(1)
    input_file_path = args.input
    with open(input_file_path, encoding="utf-8") as file:
        model, fmt = Model.load(file, args.in_format)
        if model is None:
            sys.exit(1)
        project = Project(model)
        project.default_format = fmt
        project.json_file = input_file_path

        if args.convert:
            print(
                f"write document '{args.output}' using format '{args.convert}'")

            if not formats.export_to(args.convert, model, args.output):
                print("Error")
                sys.exit(1)

        else:
            window = AnnotatorWindow(project)
            window.mainloop()

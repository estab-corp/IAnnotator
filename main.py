import json
import argparse
import os
import sys
from ui import Window
from project import Project
import formats


parser = argparse.ArgumentParser(prog='IAnnotator')
parser.add_argument('--in-format', help="json format input")
parser.add_argument('jsonfile', metavar="JSON file input file", nargs='?')
parser.add_argument(
    '--gen-coco', help="generate a coco json")
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
    json_file = args.jsonfile
    with open(json_file, encoding="utf-8") as f:
        data = json.load(f)

        model = formats.import_from("coreml", data)
        if model is None:
            sys.exit(1)
        folder = os.path.dirname(json_file)
        project = Project(model)
        project.folder = folder
        project.json_file = json_file

        if args.gen_coco:
            data = formats.export_to("coco", project)
            with open(args.gen_coco, "w", encoding="utf-8") as f:
                json.dump(data, f)
        else:
            window = Window(project)
            window.mainloop()

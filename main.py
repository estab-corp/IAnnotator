import json
import argparse
import os
import sys
from ui import Window
from project import Project
from formats import export_to, available_formats


parser = argparse.ArgumentParser(prog='IAnnotator')
parser.add_argument('--in-format', help="json format input")
parser.add_argument('jsonfile', metavar="JSON file input file", nargs='?')
parser.add_argument(
    '--gen-coco', help="generate a coco json")
parser.add_argument('--list-formats', action="store_true",
                    help="list supported formats")


def list_formats():
    for form in available_formats():
        print(form)


if __name__ == '__main__':
    args = parser.parse_args()
    if args.list_formats:
        list_formats()
        sys.exit(0)
    json_file = args.jsonfile
    with open(json_file, encoding="utf-8") as f:
        data = json.load(f)
        folder = os.path.dirname(json_file)
        project = Project(data, folder, json_file)

        if args.gen_coco:
            data = export_to("coco", project)
            with open(args.gen_coco, "w", encoding="utf-8") as f:
                json.dump(data, f)
        else:
            window = Window(project)
            window.mainloop()

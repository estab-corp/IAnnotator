import json
import argparse
import os
from ui import Window
from project import Project
from formats import export_to


parser = argparse.ArgumentParser(prog='IAnnotator')
parser.add_argument('jsonfile', metavar="JSON file")
parser.add_argument('--gen-coco', action='store_true',
                    help="generate a coco json")

if __name__ == '__main__':
    args = parser.parse_args()
    json_file = args.jsonfile
    with open(json_file, encoding="utf-8") as f:
        data = json.load(f)
        folder = os.path.dirname(json_file)
        project = Project(data, folder, json_file)

        if args.gen_coco:
            print("Generate coco")
            data = export_to("coco", project)
            print(data)
        else:
            window = Window(project)
            window.mainloop()

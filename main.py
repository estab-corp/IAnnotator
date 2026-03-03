import json
import argparse
import os
from ui import Window
from project import Project

parser = argparse.ArgumentParser(prog='IAnnotator')
parser.add_argument('jsonfile', metavar="JSON file")

if __name__ == '__main__':
    args = parser.parse_args()
    json_file = args.jsonfile
    with open(json_file, encoding="utf-8") as f:
        data = json.load(f)
        folder = os.path.dirname(json_file)
        project = Project(data, folder, json_file)
        window = Window(project)
        window.mainloop()

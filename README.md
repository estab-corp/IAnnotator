# IAnnotator

Image annotator tool. This editor helps easily creating object-detector datasets with annotations. It supports multiple formats such as coreml, coco and csv.

## Features

- Add object annotations using bounding box,
- Import/Export/Convert coreml, coco and csv formats

## Supported annotation formats

- Coco
- Core ML
- CSV containing the following columns : `filename, width, height, class, xmin, ymin, xmax, ymax`. Don't forget the header.

## Usage

to open an annotation file:

```bash
python3 main.py somefile.json
```

Note that the editor kinda expects the following layout to work:

```text
some/dir/
    annotations.json
    image0.jpg
    image1.jpg
    anotherdir/
        image2.png
        image3.png
        ...
```

So, if the `some/dir/annotations.json` is opened, all images path will be resolved starting from `some/dir/`

To export to a different annotation format, use:

```bash
python3 main.py somefile.json --convert csv out.csv
```

To create a new project from scratch:

```bash
python3 main.py
```

```bash
python3 main.py -h #help
```

## Resources

### Core ml

<https://evilmartians.com/chronicles/object-detection-with-create-ml-images-and-dataset>
<https://developer.apple.com/documentation/createml/building-an-object-detector-data-source>
<https://medium.com/hackernoon/how-to-label-data-create-ml-for-object-detection-82043957b5cb>

import os
import json
from torch.utils.data import Dataset
import torchvision.transforms.functional as F
from PIL import Image
import torch


class CustomDataset(Dataset):
    def __init__(self, root_dir, transform=None, resize=None):
        self.root_dir = root_dir
        self.transform = transform
        self.resize = resize  # (H, W) tuple if resizing

        # Load COCO annotations
        ann_path = os.path.join(root_dir, "annotations.coco.json")
        with open(ann_path, "r", encoding="utf-8") as f:
            self.coco = json.load(f)

        # Map image_id -> image file
        self.images = {img["id"]: img for img in self.coco["images"]}

        # Collect annotations by image_id
        self.annotations = {}
        for ann in self.coco["annotations"]:
            img_id = ann["image_id"]
            if img_id not in self.annotations:
                self.annotations[img_id] = []
            self.annotations[img_id].append(ann)

        self.image_ids = list(self.images.keys())

        # Build category mapping {id: name}
        self.cat_id_to_name = {cat["id"]: cat["name"]
                               for cat in self.coco["categories"]}

    def __len__(self):
        return len(self.image_ids)

    def __getitem__(self, idx):
        img_id = self.image_ids[idx]
        img_info = self.images[img_id]

        # Load image
        img_path = os.path.join(self.root_dir, img_info["file_name"])
        image = Image.open(img_path).convert("RGB")

        # Original size
        orig_w, orig_h = image.size

        # Load annotations
        anns = self.annotations.get(img_id, [])
        boxes, labels = [], []
        for ann in anns:
            x, y, w, h = ann["bbox"]
            boxes.append([x, y, x + w, y + h])
            labels.append(ann["category_id"])

        boxes = torch.as_tensor(boxes, dtype=torch.float32)
        labels = torch.as_tensor(labels, dtype=torch.int64)
        target = {"boxes": boxes, "labels": labels,
                  "image_id": torch.tensor([img_id])}

        # Resize if specified
        if self.resize:
            new_h, new_w = self.resize
            image = F.resize(image, (new_h, new_w))

            scale_x = new_w / orig_w
            scale_y = new_h / orig_h
            boxes[:, [0, 2]] = boxes[:, [0, 2]] * scale_x
            boxes[:, [1, 3]] = boxes[:, [1, 3]] * scale_y
            target["boxes"] = boxes

        if self.transform:
            image = self.transform(image)

        return image, target

# from https://blog.roboflow.com/pytorch-custom-dataset/
# and https://github.com/Neurl-LLC/roboflow-05/blob/main/Custom_Dataset_with_pytorch.ipynb

import torch
import torchvision
from PIL import Image
import torchvision.transforms as T
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from torch.utils.data import DataLoader
from torchvision.models.detection import FasterRCNN_ResNet50_FPN_Weights
from custom_dataset import CustomDataset

model_path = "model.pth"


def get_image(path: str, transform):
    image = Image.open(path).convert("RGB")
    if transform:
        image = transform(image)
    return image


def test_dataset(dataset: CustomDataset, transform):
    num_classes = len(dataset.coco["categories"]) + 1  # +1 for background
    model = torchvision.models.detection.fasterrcnn_resnet50_fpn(
        weights=FasterRCNN_ResNet50_FPN_Weights.DEFAULT)
    in_features = model.roi_heads.box_predictor.cls_score.in_features
    model.roi_heads.box_predictor = torchvision.models.detection.faster_rcnn.FastRCNNPredictor(
        in_features, num_classes)
    model.load_state_dict(torch.load(model_path, weights_only=True))
    model.eval()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    # Pick one sample from the test set
    image = get_image("../../testML/testpytorch/img3.jpg", transform)

    # Add batch dimension and send to device
    img_tensor = image.unsqueeze(0).to(device)

    # Run inference
    with torch.no_grad():
        prediction = model(img_tensor)

    # Convert back to numpy for plotting
    img_np = image.permute(1, 2, 0).numpy()

    # Plot results
    fig, ax = plt.subplots(1, figsize=(8, 8))
    ax.imshow(img_np)
    ax.set_title("Model Prediction")

    # Get predicted boxes, labels, scores
    pred_boxes = prediction[0]['boxes'].cpu()
    pred_labels = prediction[0]['labels'].cpu()
    pred_scores = prediction[0]['scores'].cpu()

    # Draw only boxes above a confidence threshold
    threshold = 0.5
    for box, label, score in zip(pred_boxes, pred_labels, pred_scores):
        if score < threshold:
            continue
        x1, y1, x2, y2 = box
        rect = patches.Rectangle(
            (x1, y1), x2 - x1, y2 - y1,
            linewidth=2, edgecolor="lime", facecolor="none"
        )
        ax.add_patch(rect)

        # Add label + score
        class_name = dataset.cat_id_to_name[label.item()]
        print(f"{class_name}: {score:.2f}")
        ax.text(
            x1, y1 - 5, f"{class_name}: {score:.2f}",
            fontsize=10, color="black",
            bbox=dict(facecolor="lime", alpha=0.5, pad=2)
        )

    plt.show()


def train_dataset(dataset: CustomDataset):
    train_loader = DataLoader(
        dataset, batch_size=2, shuffle=True, collate_fn=lambda x: tuple(zip(*x)))

    # 4. Load pre-trained Faster R-CNN model
    num_classes = len(dataset.coco["categories"]) + 1  # +1 for background
    model = torchvision.models.detection.fasterrcnn_resnet50_fpn(
        weights=FasterRCNN_ResNet50_FPN_Weights.DEFAULT)
    in_features = model.roi_heads.box_predictor.cls_score.in_features
    model.roi_heads.box_predictor = torchvision.models.detection.faster_rcnn.FastRCNNPredictor(
        in_features, num_classes)

    # 5. Move to device
    if torch.cuda.is_available():
        print("cuda is available")
    else:
        print("using cpu")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    # 6. Define optimizer
    params = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.SGD(
        params, lr=0.005, momentum=0.9, weight_decay=0.0005)

    num_epochs = 10
    print(f"start training for {num_epochs} epochs")
    for epoch in range(num_epochs):
        model.train()
        total_loss = 0
        for images, targets in train_loader:
            images = [img.to(device) for img in images]
            targets = [{k: v.to(device) for k, v in t.items()}
                       for t in targets]

            loss_dict = model(images, targets)
            losses = sum(loss for loss in loss_dict.values())

            optimizer.zero_grad()
            losses.backward()
            optimizer.step()
            total_loss += losses.item()

        print(f"Epoch {epoch+1}/{num_epochs}, Loss: {total_loss:.4f}")
    print("done")

    # 8. Save model
    torch.save(model.state_dict(), model_path)


if __name__ == "__main__":
    transform = T.Compose([
        T.ToTensor()
    ])
    dataset = CustomDataset(
        "../../testML/etiquetteDetectorDataset", transform=transform)

    # train_dataset(dataset)
    test_dataset(dataset, transform)

"""
Training script for EuroSAT satellite image classification.

Uses ResNet50 (transfer learning) to classify satellite images
into 10 land-use categories on the EuroSAT dataset.

Usage
─────
  python -m models.train_model                        # train with defaults
  python models/train_model.py                        # or directly
  python models/train_model.py --epochs 30 --bs 64    # custom settings

Outputs
───────
  models/eurosat_resnet50.pth   – best model weights
"""

import os
import sys
import time
import argparse

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

# Allow running as `python models/train_model.py`
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.dataset_loader import EuroSATDataset, EUROSAT_CLASSES

NUM_CLASSES = len(EUROSAT_CLASSES)


# ── Model ────────────────────────────────────────────────────────────────────
def build_model(num_classes=NUM_CLASSES, pretrained=True):
    """ResNet50 with frozen early layers, custom classification head."""
    import torchvision.models as models

    weights = models.ResNet50_Weights.DEFAULT if pretrained else None
    model = models.resnet50(weights=weights)

    # Freeze layers except layer4 and fc
    for name, param in model.named_parameters():
        if "layer4" not in name and "fc" not in name:
            param.requires_grad = False

    model.fc = nn.Sequential(
        nn.Linear(2048, 512),
        nn.ReLU(inplace=True),
        nn.Dropout(0.3),
        nn.Linear(512, num_classes),
    )
    return model


# ── Training Loop ────────────────────────────────────────────────────────────
def train(
    data_dir="data/satellite_images/EuroSAT",
    epochs=20,
    batch_size=32,
    lr=1e-3,
    img_size=64,
    save_path="models/eurosat_resnet50.pth",
):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    print(f"Classes ({NUM_CLASSES}): {', '.join(EUROSAT_CLASSES)}")

    # Datasets
    train_ds = EuroSATDataset(data_dir, "train.csv", img_size=img_size, augment=True)
    val_ds   = EuroSATDataset(data_dir, "validation.csv", img_size=img_size, augment=False)
    test_ds  = EuroSATDataset(data_dir, "test.csv", img_size=img_size, augment=False)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True,
                              num_workers=0, pin_memory=(device.type == "cuda"))
    val_loader   = DataLoader(val_ds, batch_size=batch_size, shuffle=False,
                              num_workers=0, pin_memory=(device.type == "cuda"))
    test_loader  = DataLoader(test_ds, batch_size=batch_size, shuffle=False,
                              num_workers=0, pin_memory=(device.type == "cuda"))

    print(f"Train: {len(train_ds)}  |  Val: {len(val_ds)}  |  Test: {len(test_ds)}")

    # Model, loss, optimizer
    model = build_model().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(
        filter(lambda p: p.requires_grad, model.parameters()), lr=lr
    )
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, patience=3, factor=0.5, min_lr=1e-6
    )

    best_val_acc = 0.0
    print()
    print("=" * 70)
    print(f"  {'Epoch':>5}  {'Train Loss':>11}  {'Train Acc':>10}  {'Val Loss':>9}  {'Val Acc':>8}  {'LR':>10}")
    print("=" * 70)

    for epoch in range(1, epochs + 1):
        t0 = time.time()

        # ── Training ──
        model.train()
        running_loss, correct, total = 0.0, 0, 0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            logits = model(images)
            loss = criterion(logits, labels)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)
            correct += (logits.argmax(1) == labels).sum().item()
            total += images.size(0)

        train_loss = running_loss / total
        train_acc = correct / total

        # ── Validation ──
        model.eval()
        val_loss, val_correct, val_total = 0.0, 0, 0
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                logits = model(images)
                val_loss += criterion(logits, labels).item() * images.size(0)
                val_correct += (logits.argmax(1) == labels).sum().item()
                val_total += images.size(0)

        val_loss /= val_total
        val_acc = val_correct / val_total
        scheduler.step(val_loss)

        elapsed = time.time() - t0
        lr_now = optimizer.param_groups[0]["lr"]

        print(
            f"  {epoch:5d}  {train_loss:11.4f}  {train_acc:9.2%}  "
            f"{val_loss:9.4f}  {val_acc:7.2%}  {lr_now:10.2e}  ({elapsed:.1f}s)"
        )

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), save_path)
            print(f"         ✓ Saved best model → {save_path}  (val acc {val_acc:.2%})")

    # ── Final Test Evaluation ──
    print()
    print("=" * 70)
    print("  Final Test Evaluation")
    print("=" * 70)
    model.load_state_dict(torch.load(save_path, weights_only=True))
    model.eval()

    test_correct, test_total = 0, 0
    class_correct = [0] * NUM_CLASSES
    class_total = [0] * NUM_CLASSES

    with torch.no_grad():
        for images, labels in test_loader:
            images, labels = images.to(device), labels.to(device)
            preds = model(images).argmax(1)
            test_correct += (preds == labels).sum().item()
            test_total += images.size(0)
            for p, l in zip(preds, labels):
                class_total[l.item()] += 1
                if p.item() == l.item():
                    class_correct[l.item()] += 1

    test_acc = test_correct / test_total
    print(f"\n  Overall Test Accuracy: {test_acc:.2%}  ({test_correct}/{test_total})")
    print(f"\n  {'Class':<25} {'Accuracy':>9}  {'Correct':>8}  {'Total':>6}")
    print("  " + "─" * 52)
    for i, name in enumerate(EUROSAT_CLASSES):
        if class_total[i] > 0:
            acc = class_correct[i] / class_total[i]
            print(f"  {name:<25} {acc:>8.2%}  {class_correct[i]:>8}  {class_total[i]:>6}")

    print()
    print(f"  Best validation accuracy: {best_val_acc:.2%}")
    print(f"  Model saved to: {save_path}")
    print("  Training complete.")

    return test_acc


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train EuroSAT classifier")
    parser.add_argument("--data", default="data/satellite_images/EuroSAT",
                        help="Path to EuroSAT dataset directory")
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--bs", type=int, default=32, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--img-size", type=int, default=64)
    parser.add_argument("--save", default="models/eurosat_resnet50.pth")
    args = parser.parse_args()

    train(
        data_dir=args.data,
        epochs=args.epochs,
        batch_size=args.bs,
        lr=args.lr,
        img_size=args.img_size,
        save_path=args.save,
    )

# models/

This directory is a placeholder for **trained model weights and checkpoints**.

> Status: **planned**. No model weights are committed to this repository.

## Rules

- Do **not** commit model weights, checkpoints, or exported models here
  (`.pt`, `.pth`, `.onnx`, `.engine`, `.ckpt`, etc.).
- Everything in this folder is ignored by Git except this `README.md`
  (see the project [`.gitignore`](../.gitignore)).
- Large weights should be shared through an external location (release asset,
  cloud storage, or model registry) and referenced here.

## Expected layout (local only)

```text
models/
  pretrained/   # downloaded base weights (e.g. YOLO base model)
  trained/      # weights produced by our own training runs
```

## Tracking

| Model            | Base       | Purpose                  | Location / Link |
| ---------------- | ---------- | ------------------------ | --------------- |
| PPE detector     | YOLO (TBD) | Detect PPE / violations  | TBD             |

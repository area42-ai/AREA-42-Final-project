# data/

This directory is a placeholder for **local datasets used during development**.

> Status: **planned**. No datasets are committed to this repository.

## Rules

- Do **not** commit raw datasets, images, videos, or annotations here.
- Everything in this folder is ignored by Git except this `README.md`
  (see the project [`.gitignore`](../.gitignore)).
- Each team member keeps their own local copy of the data.

## Expected layout (local only)

```text
data/
  raw/        # original, unmodified source data
    ppe_detection_v1/   # PPE detection dataset (see metadata below)
  interim/    # partially processed data
  processed/  # data ready for training / evaluation
```

## Candidate dataset: PPE detection

The PPE detection dataset is **downloaded locally** into
`data/raw/ppe_detection_v1/` and is **not committed to Git**. Download it
manually and place it there to reproduce the local setup.

### Reproducibility metadata

| Field      | Value                                                         |
| ---------- | ------------------------------------------------------------ |
| Source     | Roboflow                                                     |
| Workspace  | testcasque                                                   |
| Project    | ppe-detection-qlq3d                                          |
| Version    | 1                                                           |
| License    | CC BY 4.0                                                    |
| URL        | https://universe.roboflow.com/testcasque/ppe-detection-qlq3d |
| Format     | YOLOv8                                                       |
| Local path | `data/raw/ppe_detection_v1/`                                |

### Classes (10)

```text
boots, gloves, goggles, helmet, no-boots, no-gloves, no-goggles, no-helmet, no-vest, vest
```

> Download datasets manually into this folder. Do not add them to version
> control, and do not commit any private API keys or download tokens.

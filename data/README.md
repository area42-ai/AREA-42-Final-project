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

# Data Directory

This directory is intended for local datasets, evaluation data, and demo videos. 

**Important:** According to the project's Asset Policy and MVP Strategy (Decision 13), no raw datasets, videos, model weights, or other large assets are committed to this Git repository. All data files are added to the `.gitignore`.

## External Storage

The test videos, are securely stored outside of Git in our external Google Drive folder.

* **Drive Folder Name:** `data-AREA42`
* **Link:** https://drive.google.com/drive/folders/1YeeXtYlo_2bvwRsKH2jY77faotBf1hdV?usp=sharing

**Evaluation Dataset:**
 Created a diverse, manually annotated PPE video evaluation set with ground-truth JSON files to test our pipeline against real-world scenarios (including compliance, violations, and occlusions). These assets are securely stored on Google Drive outside of the repository.
 
**Real-world scenarios:**
1. One worker wears a hard hat during the entire video.
2. One worker is without a hard hat during the entire video.
3. Worker starts with a hard hat, removes it, and later wears it again.
4. Worker enters without a hard hat and puts it on after several seconds.
5. Worker removes the hard hat and does not wear it again before the video ends.
6. Two workers: one compliant and one without a hard hat.
7. A hard hat is held in the hands but is not worn.
8. Hands or another object temporarily block the worker's head.
9. Worker leaves the frame while the violation is active.
10. Difficult conditions: distant camera, blur, low light, partial body visibility, unusual angle, or short transitions.
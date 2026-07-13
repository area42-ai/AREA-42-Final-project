from ultralytics import YOLO
from huggingface_hub import hf_hub_download

# Downloading and loading the model
model_path = hf_hub_download(repo_id="melihuzunoglu/ppe-detection", filename="best.pt")
model = YOLO(model_path)

# Run inference
results = model.predict(source="your_image_here.jpeg", conf=0.25, save=True)
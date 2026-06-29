import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google import genai

load_dotenv()

MODEL = "gemma-4-26b-a4b-it"

PROMPT = """
You are an intelligent AI assistant monitoring workplace safety.

Analyze the uploaded video in its entirety.

Detect every time interval during which a worker is not wearing a safety helmet (hard hat).

Rules:
- Holding the helmet in hand does NOT count as wearing it.
- A helmet lying nearby does NOT count.
- The time during which the worker is putting the helmet on must still be counted as a violation.
- Only stop the violation when the helmet is fully worn.
- Analyze the entire video context.

Return ONLY valid JSON.

{
  "video_duration_seconds": 0.0,
  "incident_count": 0,
  "incidents": [
    {
      "incident_id": 1,
      "type": "missing_hard_hat",
      "status": "resolved",
      "start_time_seconds": 0.0,
      "end_time_seconds": 0.0,
      "duration_seconds": 0.0,
      "message": ""
    }
  ]
}
""".strip()


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Native video understanding with Gemma 4"
    )

    parser.add_argument(
        "--video",
        required=True,
        help="Path to MP4 video"
    )

    parser.add_argument(
        "--output-dir",
        default="results",
        help="Directory for results"
    )

    return parser.parse_args()


def extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()

    cleaned = re.sub(r"^```json\s*", "", cleaned)
    cleaned = re.sub(r"^```\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(
            "The model response does not contain a JSON object."
        )

    return json.loads(cleaned[start:end + 1])


def wait_until_ready(client, file_obj):
    print("Waiting for video processing...")

    while True:
        current = client.files.get(name=file_obj.name)

        state = getattr(current, "state", None)

        if state:
            state_name = str(state).upper()

            print(f"Current state: {state_name}")

            if "ACTIVE" in state_name:
                return current

            if "FAILED" in state_name:
                raise RuntimeError("Video processing failed.")

        time.sleep(5)


def remove_audio_with_ffmpeg(input_path: Path) -> Path:
    """FFmpeg istifadə edərək audio-nu silir"""
    # imageio_ffmpeg-in ffmpeg faylını tap
    try:
        import imageio_ffmpeg
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        print(f"FFmpeg found at: {ffmpeg_path}")
    except:
        # Əgər imageio_ffmpeg tapılmazsa, sadəcə ffmpeg komandasını işlət
        ffmpeg_path = "ffmpeg"
    
    temp_dir = Path(tempfile.gettempdir())
    output_path = temp_dir / f"{input_path.stem}_no_audio{input_path.suffix}"
    
    # FFmpeg komandasını işlət
    cmd = [
        ffmpeg_path,
        "-i", str(input_path),
        "-c", "copy",
        "-an",  # Audio-nu sil
        "-y",   # Mövcud faylı üzərinə yaz
        str(output_path)
    ]
    
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            print(f"FFmpeg error: {result.stderr}")
            # Əgər uğursuz olarsa, orijinal faylı qaytar
            print("FFmpeg failed. Using original video.")
            return input_path
        
        print(f"Audio removed successfully: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error running FFmpeg: {e}")
        print("Using original video.")
        return input_path


def main():
    args = parse_arguments()

    video_path = Path(args.video)

    if not video_path.exists():
        raise FileNotFoundError(video_path)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY environment variable not found."
        )

    client = genai.Client(api_key=api_key)

    # Audio-nu sil (FFmpeg ilə)
    temp_video_path = remove_audio_with_ffmpeg(video_path)
    use_temp = temp_video_path != video_path
    
    try:
        print("Uploading video...")

        uploaded_file = client.files.upload(
            file=str(temp_video_path)
        )

        uploaded_file = wait_until_ready(
            client,
            uploaded_file
        )

        print("Starting video analysis...")

        response = client.models.generate_content(
            model=MODEL,
            contents=[
                uploaded_file,
                PROMPT
            ]
        )

        text = response.text

        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            result = extract_json(text)

        output_file = (
            output_dir /
            f"{video_path.stem}_analysis.json"
        )

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(
                result,
                f,
                indent=2,
                ensure_ascii=False
            )

        print("\nAnalysis completed.")
        print(f"Saved: {output_file}")

        # Nəticəni ekranda göstər
        print("\nResults:")
        print(f"Video duration: {result.get('video_duration_seconds', 0)} seconds")
        print(f"Incident count: {result.get('incident_count', 0)}")
        for incident in result.get("incidents", []):
            print(f"  - Incident {incident.get('incident_id')}: {incident.get('start_time_seconds')}s - {incident.get('end_time_seconds')}s")

    except Exception as e:
        print(f"\nError occurred: {e}")
        if hasattr(e, 'response'):
            print(f"Response: {e.response}")
        raise

    finally:
        # Müvəqqəti faylı sil
        if use_temp and temp_video_path.exists():
            try:
                print(f"\nDeleting temporary file: {temp_video_path}")
                temp_video_path.unlink()
                print("Temporary file deleted.")
            except Exception as e:
                print(f"Delete warning: {e}")

        # Upload edilmiş faylı sil
        try:
            print("Deleting uploaded video...")
            client.files.delete(name=uploaded_file.name)
            print("Uploaded file deleted.")
        except Exception as e:
            print(f"Delete warning: {e}")


if __name__ == "__main__":
    main()
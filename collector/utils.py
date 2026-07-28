import json
import os
import tempfile

from .config import OUTPUT_FILE

def save_json(data):
    if not OUTPUT_FILE:
        return

    output_dir = os.path.dirname(os.path.abspath(OUTPUT_FILE))
    os.makedirs(output_dir, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output_dir,
            delete=False,
        ) as f:
            temp_path = f.name
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_path, OUTPUT_FILE)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)


    print(
        f"Saved {len(data['tunnels'])} tunnels",
        flush=True
    )

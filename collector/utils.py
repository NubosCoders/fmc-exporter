from .config import OUTPUT_FILE
import json

def save_json(data):

    with open(
        OUTPUT_FILE,
        "w"
    ) as f:

        json.dump(
            data,
            f,
            indent=2
        )


    print(
        f"Saved {len(data['tunnels'])} tunnels",
        flush=True
    )

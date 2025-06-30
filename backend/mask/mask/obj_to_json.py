import re
import json
from pathlib import Path

def parse_obj_file(path):
    path = Path(path)
    lines = path.read_text().splitlines()
    objects = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("@"):
            obj_type = "TARGET"
            line = line[1:]
        elif line.startswith("*"):
            obj_type = "ALIGN"
            line = line[1:]
        else:
            continue  # skip invalid or unmarked lines

        match = re.match(
            r"(?P<name>\S+)\s+(?P<ra>[\d\.]+)\s+(?P<dec>[-\d\.]+)\s+Pri=(?P<priority>[-\d\.]+)(?:\s+alen=(?P<a_len>[\d\.]+)\s+blen=(?P<b_len>[\d\.]+))?",
            line
        )

        if match:
            obj = {
                "name": match.group("name"),
                "type": obj_type,
                "ra": float(match.group("ra")),
                "dec": float(match.group("dec")),
                "priority": float(match.group("priority")),
            }
            if match.group("a_len") and match.group("b_len"):
                obj["a_len"] = float(match.group("a_len"))
                obj["b_len"] = float(match.group("b_len"))
            objects.append(obj)

    return objects

# === Example Usage ===
obj_file_path = "/Users/maylinchen/Downloads/DCM5V5E.obj"
output_path = Path("/Users/maylinchen/Downloads/mask/backend/mask/maskgen_api/test_files/DCM5V5E.json")

parsed_objects = parse_obj_file(obj_file_path)

print(json.dumps(parsed_objects, indent=2))
output_path.write_text(json.dumps(parsed_objects, indent=2))

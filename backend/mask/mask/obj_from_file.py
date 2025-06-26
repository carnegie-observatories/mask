import re
import json
from pathlib import Path

def parse_obj_file(path):
    path = Path(path)
    lines = path.read_text().splitlines()
    objects = []

    for i in range(0, len(lines), 2):  # Assuming 2-line entries
        header = lines[i].strip()
        if not header.startswith("@"):
            continue

        match = re.match(
            r"@(?P<name>\S+)\s+(?P<ra>[\d\.]+)\s+(?P<dec>[-\d\.]+)\s+Pri=(?P<priority>[-\d\.]+)\s+alen=(?P<a_len>[\d\.]+)\s+blen=(?P<b_len>[\d\.]+)",
            header
        )
        if match:
            obj = {
                "name": match.group("name"),
                "ra": float(match.group("ra")),
                "dec": float(match.group("dec")),
                "priority": float(match.group("priority")),
                "a_len": float(match.group("a_len")),
                "b_len": float(match.group("b_len"))
            }
            objects.append(obj)
    return objects

# === Example Usage ===
# Replace this with your actual file path
obj_file_path = "/Users/maylinchen/Downloads/DCM5V5E.obj"
output_path = Path("/Users/maylinchen/Downloads/mask/backend/mask/maskgen_api/test_files/DCM5V5E.json")

parsed_objects = parse_obj_file(obj_file_path)

# Print or save as JSON
print(json.dumps(parsed_objects, indent=2))
output_path.write_text(json.dumps(parsed_objects, indent=2))
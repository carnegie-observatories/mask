from .models import Object, ObjectList
import re
from pathlib import Path
import os
from astropy.coordinates import Angle
import astropy.units as u


def to_deg(ra, dec):
    if "." not in str(ra):
        ra = Angle(ra, unit=u.hourangle).degree
    else:
        ra = float(ra)
    if "." not in str(dec):
        dec = Angle(dec, unit=u.degree).degree
    else:
        dec = float(dec)
    return ra, dec


def categorize_objs(mask, file_path):
    lines = Path(file_path).read_text().splitlines()
    for line in lines:
        # get obj name
        match = re.match(r"[@\*](\S+)", line)
        if match:
            try:
                obj = Object.objects.get(name=match.group(1))
                if re.search(r"Use=\d+", line):
                    mask.objects_list.add(obj)
                else:
                    mask.excluded_obj_list.add(obj)
                mask.save()
            except Object.DoesNotExist:
                mask.delete()
                return False, f"warning: object with name '{match.group(1)}' not found."
    return True, "yay it worked"


def obj_to_json(file_bytes):
    text = file_bytes.decode("utf-8")
    lines = text.splitlines()
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
            line,
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


"""
# === Example Usage ===
obj_file_path = "/Users/maylinchen/Downloads/DCM5V5E.obj"
output_path = Path("/Users/maylinchen/Downloads/mask/backend/mask/maskgen_api/test_files/DCM5V5E.json")

parsed_objects = parse_obj_file(obj_file_path)

print(json.dumps(parsed_objects, indent=2))
output_path.write_text(json.dumps(parsed_objects, indent=2))
"""


def generate_obj_file(user_id, proj_name, filename, objects):
    """
    Generates a .obj file following Carnegie OBS formatting

    takes optional parameters for selected objects as well. Stores in obj_files folder

    Args:
        filename (str): name of the ob
        objects (str): list of json objects of all the objects

    Returns:
        str: path to obj file
    """
    script_dir = os.path.dirname(__file__)
    path = os.path.join(script_dir, "obj_files", user_id, proj_name, f"{filename}.obj")
    os.makedirs(os.path.join(script_dir, "obj_files", user_id), exist_ok=True)
    os.makedirs(
        os.path.join(script_dir, "obj_files", user_id, proj_name), exist_ok=True
    )

    with open(path, "w") as file:
        file.write("&RADEGREE\n")
        if not isinstance(objects, list):
            objects = list(
                ObjectList.objects.get(name=objects).objects_list.values_list(
                    "id", flat=True
                )
            )
        for id in objects:
            obj = Object.objects.get(id=id)
            if obj.type != "GUIDE":
                new_line = f"{obj.name} {obj.right_ascension} {obj.declination} Pri={float(obj.priority)}"
                if obj.aux:
                    if hasattr(obj.aux, "use"):
                        new_line += f" use={obj.aux.use}"
                    if hasattr(obj.aux, "width"):
                        new_line += f" width={obj.aux.width}"
                    if hasattr(obj.aux, "shape"):
                        new_line += f" shape={obj.aux.shape}"
                    if hasattr(obj.aux, "a_len"):
                        new_line += f" a_len={obj.aux.a_len}"
                    if hasattr(obj.aux, "b_len"):
                        new_line += f" b_len={obj.aux.b_len}"
                    if hasattr(obj.aux, "tilt"):
                        new_line += f" tilt={obj.aux.tilt}"
                    if hasattr(obj.aux, "pa"):
                        new_line += f" pa={obj.aux.pa}"

                if obj.type == "ALIGN":
                    new_line = "*" + new_line
                elif obj.type == "TARGET":
                    new_line = "@" + new_line

                file.write(new_line + "\n")

    return f"obj_files/{user_id}/{proj_name}/{filename}.obj"


def generate_obs_file(user_id, proj_name, instrument_setup, obj_file_paths):
    """
    Generates a .obs file following Carnegie OBS formatting

    takes optional parameters for selected objects as well. Stores in obs_files folder

    Args:
        instrument_setup (json): json of all the params needed for instrument setup. See instrum_setup_ex.json for example
        obj_file_paths (str): list of paths to the .obj files

    Returns:
        str: path to obs file
    """
    script_dir = os.path.dirname(__file__)
    os.makedirs(os.path.join(script_dir, "obs_files", user_id), exist_ok=True)
    os.makedirs(
        os.path.join(script_dir, "obs_files", user_id, proj_name), exist_ok=True
    )
    obs_header = f"""#Obs file ({instrument_setup['filename']}.obs)
# Written By:  IntGui 4.70 
! Edited {instrument_setup['edit_date']} By Observer Interface GUI version 4.70.31
OBSERVER  {instrument_setup['observer']}
FILENAME  {instrument_setup['filename']}
TITLE   {instrument_setup['title']}
CENTER   {instrument_setup['center_ra']} {instrument_setup['center_dec']}
EQUINOX  {instrument_setup['equinox']:.5f}
POSITION {instrument_setup['position']:.5f}
DREF  {instrument_setup['dref']}
HANGLE {instrument_setup['hangle']}
#! No rotator warnings above horizon.
"""
    for gs in instrument_setup["guide_stars"]:
        obs_header += (
            f"{gs['name']} {gs['ra']}   {gs['dec']}  {gs['equinox']:.3f}  {gs['id']}\n"
        )
    """
    REFHOLE: 
        Hole width, decimal arcseconds.  Default 5.803 (about 2.0 mm).
        Hole shape code, integer.  0=circle, 1=square, 2=rectangle, 3=special.
        The default shape is square.
        Hole A length and B length.  For circle or square shapes, these will
        be ignored and 1/2 the width used instead.
        Hole orientation angle, decimal degrees.
    """
    obs_header += f"""WLIMIT  {instrument_setup['wlimit_low']:.1f} {instrument_setup['wlimit_high']:.1f}
Wavelength  {instrument_setup['wavelength']:.2f}
PDECIDE  {instrument_setup['pdecide']:.2f}
TELESCOPE  {instrument_setup['telescope']}
INSTRUMENT {instrument_setup['instrument']}
DISPERSER  {instrument_setup['disperser']}
SLITSIZE  {instrument_setup['slit_width']:.3f} {instrument_setup['a_len']:.3f} {instrument_setup['b_len']:.3f} {instrument_setup['slit_tilt']:.3f} 
REFHOLE   {instrument_setup['refhole_width']:.3f} {instrument_setup['refhole_shape']} {instrument_setup['refhole_a_len']:.3f} {instrument_setup['refhole_b_len']:.3f} {instrument_setup['refhole_orient_deg']:.3f}
OVERLAP    {instrument_setup['overlap']:.2f}
EXORDER  {instrument_setup['exorder']}
DATE {instrument_setup['date']}
#  Object file list
"""
    for obj_path in obj_file_paths:
        obs_header += f"OBJFILE  {obj_path}\n"
    script_dir = os.path.dirname(__file__)

    path = os.path.join(
        script_dir,
        "obs_files",
        user_id,
        proj_name,
        f"{instrument_setup['filename']}.obs",
    )

    with open(path, "w") as file:
        file.write(obs_header)
    return path

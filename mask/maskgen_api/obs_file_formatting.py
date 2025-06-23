from .models import Object
def generate_obj_file(filename, objects):
    """
    Generates a .obj file following Carnegie OBS formatting

    takes optional parameters for selected objects as well. Stores in obj_files folder

    Args:
        filename (str): name of the ob
        objects (str): list of json objects of all the objects

    Returns:
        str: path to obj file
    """
    path = f"obj_files/{filename}.obs"
    with open(f"{filename}.obj", 'w') as file:
        file.write("&RADEGREE\n")
        for id in objects: 
            obj = Object.objects.get(id)
            new_line = f"{obj.name} {obj.right_ascension} {obj.declination} Pri={float(obj.priority)}"
            if obj.aux:
                if hasattr(obj.aux, 'use'):
                    new_line += f" use={obj.aux.use}"
                if hasattr(obj.aux, 'width'):
                    new_line += f" width={obj.aux.width}"
                if hasattr(obj.aux, 'shape'):
                    new_line += f" shape={obj.aux.shape}"
                if hasattr(obj.aux, 'a_len'):
                    new_line += f" a_len={obj.aux.a_len}"
                if hasattr(obj.aux, 'b_len'):
                    new_line += f" b_len={obj.aux.b_len}"
                if hasattr(obj.aux, 'tilt'):
                    new_line += f" tilt={obj.aux.tilt}"
                if hasattr(obj.aux, 'pa'):
                    new_line += f" pa={obj.aux.pa}"
            
            if obj.type == "ALIGN":
                new_line = "*" + new_line
            elif obj.type == "TARGET":
                new_line = "@" + new_line
            
            file.write(new_line + "\n")
    return path

def generate_obs_file(instrument_setup, obj_file_paths):
    obs_header = f"""#Obs file ({instrument_setup.filename}.obs)
# Written By:  IntGui 4.70 
! Edited {instrument_setup.edit_date} By Observer Interface GUI version 4.70.31
OBSERVER  {instrument_setup.observer}
FILENAME  {instrument_setup.filename}
TITLE   {instrument_setup.title}
CENTER   {instrument_setup.center_ra} {instrument_setup.center_dec}
EQUINOX  {instrument_setup.equinox:.5f}
POSITION {instrument_setup.position:.5f}
DREF  {instrument_setup.dref}
HANGLE {instrument_setup.hangle}
#! No rotator warnings above horizon.
"""
    for gs in instrument_setup.guide_stars:
        obs_header += f"{gs['name']} {gs['ra']}   {gs['dec']}  {gs['equinox']:.3f}  {gs['id']}\n"
    """
    REFHOLE: 
        Hole width, decimal arcseconds.  Default 5.803 (about 2.0 mm).
        Hole shape code, integer.  0=circle, 1=square, 2=rectangle, 3=special.
        The default shape is square.
        Hole A length and B length.  For circle or square shapes, these will
        be ignored and 1/2 the width used instead.
        Hole orientation angle, decimal degrees.
    """
    obs_header += f"""WLIMIT  {instrument_setup.wlimit_low:.1f} {instrument_setup.wlimit_high:.1f}
Wavelength  {instrument_setup.wavelength:.2f}
PDECIDE  {instrument_setup.pdecide:.2f}
TELESCOPE  {instrument_setup.telescope}
INSTRUMENT {instrument_setup.instrument}
DISPERSER  {instrument_setup.disperser}
SLITSIZE  {instrument_setup.slit_width:.3f} {instrument_setup.a_len:.3f} {instrument_setup.b_len:.3f} {instrument_setup.slit_tilt:.3f} 
REFHOLE   {instrument_setup.refhole_width:.3f} {instrument_setup.refhole_shape} {instrument_setup.refhole_a_len:.3f} {instrument_setup.refhole_b_len:.3f} {instrument_setup.refhole_orient_deg:.3f}
OVERLAP    {instrument_setup.overlap:.2f}
EXORDER  {instrument_setup.exorder}
DATE {instrument_setup.date}
#  Object file list
"""
    for obj_path in obj_file_paths:
        obs_header += f"OBJFILE  {obj_path}.obj\n"
    with open(f"obs_files/{instrument_setup.filename}.obs", "w") as file:
        file.write(obs_header)
    return f"obs_files/{instrument_setup.filename}.obs"

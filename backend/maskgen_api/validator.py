import math
from .obs_file_formatting import to_deg

pdx_lat = -29.01418  # las campanas coordinate


# TODO: figure out what hrf is set to (defaults to 30 but other times is recalculated?)
def validate(instrum_setup):
    hrf = 30
    if hrf > 24.0:
        return True, "OK"
    else:
        # defc: Dec. field center in degrees
        defc = instrum_setup["center_dec"]
        if ":" in defc:
            _, defc = to_deg("10:00:18.500", instrum_setup["center_dec"])
        else:
            defc = float(defc)

        hk = gsda(30.0, defc, pdx_lat)
        if math.fabs(hrf) < hk:
            return False, "URGENT WARNING: ROTATOR!"

        return False, "WARNING ROTATOR!"


def gsda(a, d, g):
    """
    Compute the semi-diurnal arc in hours.
    """
    Degree = math.pi / 180.0
    Hour = 15.0 * Degree  # 1 hour = 15 degrees in RA

    sd = math.sin(d)
    cd = math.cos(d)
    sp = math.sin(g * Degree)
    cp = math.cos(g * Degree)
    sal = math.sin(a * Degree)

    if cd < 0.001:
        cd = 0.001

    csd = (sal - sd * sp) / (cd * cp)
    if csd < -1.0:
        csd = -1.0
    if csd > 1.0:
        csd = 1.0

    return math.acos(csd) / Hour  # in hours

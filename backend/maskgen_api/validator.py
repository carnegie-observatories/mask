import math

pdx_lat = -29.01418  # las campanas coordinate


def validate(instrum_setup):
    hrf = instrum_setup["hangle"]
    if hrf > 24.0:
        return True, "OK"
    else:
        # defc: Dec. field center in degrees
        defc = instrum_setup["center_dec"]
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

    sd = math.sin(d * Degree)
    cd = math.cos(d * Degree)
    sp = math.sin(g * Degree)
    cp = math.cos(g * Degree)
    sal = math.sin(a * Degree)

    if cd < 0.001:
        cd = 0.001

    csd = (sal - sd * sp) / (cd * cp)
    csd = max(-1.0, min(1.0, csd))

    return math.acos(csd) / Hour  # in hours

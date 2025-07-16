def validate(instrum_setup):
    return True


def check_rotator_conflict(rotator_angle, declination, altitude):
    """
    Validates rotator setup for a telescope instrument.

    Args:
        rotator_angle (float): angle in degrees (0–360)
        declination (float): object's declination in degrees
        altitude (float): object's altitude in degrees

    Returns:
        dict with 'status', 'message', and 'suggested_angle' if applicable
    """
    # Normalize angle to -180 to +180 range
    normalized_angle = ((rotator_angle + 180) % 360) - 180

    # Check if angle is outside of rotator's mechanical range
    if abs(normalized_angle) > 180:
        return {
            "status": "error",
            "message": f"Rotator angle {rotator_angle}° exceeds +/-180° range.",
            "suggested_angle": (rotator_angle + 180) % 360,
        }

    # Conflict due to rotation limit during observation
    if abs(normalized_angle) == 180:
        if altitude > 30:
            return {
                "status": "warning-red",
                "message": "!ROTATOR! Conflict with object above 30° altitude.",
                "suggested_angle": (rotator_angle + 180) % 360,
            }
        elif altitude > 0:
            return {
                "status": "warning",
                "message": "!ROTATOR! Conflict with object above horizon.",
                "suggested_angle": (rotator_angle + 180) % 360,
            }

    # Default angle recommendation
    if declination > -29 and rotator_angle == 90:
        return {"status": "ok", "message": "(OK)"}
    elif declination < -29 and rotator_angle == 270:
        return {"status": "ok", "message": "(OK)"}
    elif declination < -29 and rotator_angle == 90:
        return {
            "status": "warning",
            "message": "Declination < -29°: consider using rotator angle 270° instead of 90°.",
            "suggested_angle": 270,
        }

    return {"status": "ok", "message": "(OK)"}

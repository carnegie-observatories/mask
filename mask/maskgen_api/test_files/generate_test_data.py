from maskgen_api.models import Mask, Object

""" Reset db
rm db.sqlite3                  
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc"  -delete
"""

""" Migrate again
python manage.py makemigrations         
python manage.py migrate         
"""

# create test guide star objects
guide_star1 = Object.objects.create(
    name='GS1', type='GUIDE', right_ascension=10.0, declination=20.0,
    priority=1, a_len=1.2, b_len=0.8
)
guide_star2 = Object.objects.create(
    name='GS2', type='GUIDE', right_ascension=11.0, declination=21.0,
    priority=2, a_len=1.1, b_len=0.9
)

# create instrument setup
instrument_setup = {
    "filter_low" : 2000
}

# create JSON fields for features (slits and holes)
features = [
    {"id": 1, "type": "slit", "x": 123.4, "y": 567.8, "length": 10.5, "width": 1.2},
    {"id": 2, "type": "slit", "x": 333.4, "y": 33.8, "length": 3.5, "width": 1.2},
    {"id": 3, "type": "hole", "x": 123.4, "y": 567.8, "diameter": 0.8},
    {"id": 4, "type": "hole", "x": 333.4, "y": 33.8, "diameter": 2.8},
]

# create the mask
mask = Mask.objects.create(
    name='TEST_MASK_001',
    status='Test mask creation',
    features=features,
    instrument_setup=instrument_setup
)

# Step 4: Add guide stars to the mask
mask.objects_list.add(guide_star1, guide_star2)

print(f"Created mask: {mask}")

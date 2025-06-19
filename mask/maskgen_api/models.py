from django.db import models

# Enums
class Filters(models.TextChoices):
    U = 'U', 'U-band'
    B = 'B', 'B-band'
    V = 'V', 'V-band'
    I = 'I', 'I-band'
    OTHER = 'OTHER', 'Other'

class Instrument(models.TextChoices):
    IMACS_F4 = 'IMACS f/4'
    IMACS_F2 = 'IMACS f/2'

# Models
# add more info later 
class Filter(models.Model):
    name = models.CharField(max_length=50, choices=Filters.choices)

    def __str__(self):
        return self.name


class Disperser(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name
    
class InstrumentConfig(models.Model):
    instrument = models.CharField(max_length=20, choices=Instrument.choices)
    version = models.CharField(max_length=50)
    available_filters = models.ManyToManyField(Filter, blank=True)
    available_dispersers = models.ManyToManyField(Disperser, blank=True)

    def __str__(self):
        return f"{self.instrument} v{self.version}"

class Mask(models.Model):
    name = models.CharField(max_length=20, primary_key=True)
    status = models.CharField(max_length=100)
    features = models.JSONField()
    objects_list = models.ManyToManyField('Object', blank=True)
    instrument_config = models.ForeignKey('InstrumentConfig', on_delete=models.SET_NULL, null=True)
    instrument_setup = models.JSONField()

    def __str__(self):
        return f"Mask {self.name}"  
    
# class InstrumentSetup(models.Model):
#     instrument_config = models.ForeignKey('InstrumentConfig', on_delete=models.SET_NULL, null=True)
#     filter_band = models.ForeignKey('Filter', on_delete=models.SET_NULL, null=True)
#     dispersor = models.ForeignKey('Grism', on_delete=models.SET_NULL, null=True)
#     nod_and_shuffle_mode = models.BooleanField(default=False)
#     alpha_offset = models.FloatField()
#     delta_offset = models.FloatField()
#     proper_motion_alpha = models.FloatField()
#     proper_motion_delta = models.FloatField()

#     def __str__(self):
#         return f"InstrumentSetup {self.id} for {self.instrument_config}"
      
class Object(models.Model):
    TYPE_CHOICES = [
        ('GUIDE', 'Guider'),
        ('ALIGN', 'Alignment'),
        ('TARGET', 'Target'),
    ]

    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    right_ascension = models.FloatField()
    declination = models.FloatField()
    priority = models.IntegerField(default=0.0)
    a_len = models.FloatField(null=True, blank=True)
    b_len = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.type} Object {self.name}"
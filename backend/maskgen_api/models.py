from django.db import models


class Instrument(models.TextChoices):
    IMACS_F4 = "IMACS f/4"
    IMACS_F2 = "IMACS f/2"


class Status(models.TextChoices):
    DRAFT = "draft", "Draft"
    FINALIZED = "finalized", "Finalized (sent to be cut)"
    COMPLETED = "completed", "Completed (mask has been cut successfully)"


# Models
class Project(models.Model):
    name = models.CharField()
    user_id = models.CharField()
    center_ra = models.FloatField()
    center_dec = models.FloatField()
    obj_list = models.ForeignKey(
        "ObjectList", on_delete=models.SET_NULL, null=True, blank=True
    )
    masks = models.ManyToManyField("Mask", blank=True)
    images = models.ManyToManyField("Image", blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name", "user_id"], name="unique_project_per_user"
            )
        ]


class Image(models.Model):
    name = models.CharField(unique=True)
    image = models.ImageField(upload_to="uploads/")


class InstrumentConfig(models.Model):
    instrument = models.CharField(max_length=20, choices=Instrument.choices)
    version = models.IntegerField()
    filters = models.JSONField()
    dispersers = models.JSONField()
    aux = models.JSONField()

    def __str__(self):
        return f"{self.instrument} v{self.version}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["instrument", "version"], name="unique_instrument_version"
            )
        ]


class Mask(models.Model):
    name = models.CharField(max_length=20)
    user_id = models.CharField(max_length=100)
    status = models.CharField(
        max_length=100, choices=Status.choices, default=Status.DRAFT
    )
    features = models.JSONField()  # slits and holes
    objects_list = models.ManyToManyField(
        "Object", blank=True, related_name="objs_on_mask"
    )  # guide and alignment stars
    excluded_obj_list = models.ManyToManyField(
        "Object", blank=True, related_name="objs_not_on_mask"
    )  # objs left out of the mask
    instrument_version = models.IntegerField()
    instrument_setup = models.JSONField()

    def __str__(self):
        return f"Mask {self.name}"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user_id", "name"], name="unique_mask_name")
        ]


class Object(models.Model):
    TYPE_CHOICES = [
        ("GUIDE", "Guider"),
        ("ALIGN", "Alignment"),
        ("TARGET", "Target"),
    ]

    name = models.CharField(max_length=100)
    user_id = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    right_ascension = models.FloatField()
    declination = models.FloatField()
    priority = models.IntegerField(default=0.0)
    aux = models.JSONField(null=True)  # a_len, b_len

    def __str__(self):
        return f"{self.type} Object {self.name}"


# object list: user_id, name, id, objects
class ObjectList(models.Model):
    user_id = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    objects_list = models.ManyToManyField("Object", blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name", "user_id"], name="unique_obj_list_per_user"
            )
        ]

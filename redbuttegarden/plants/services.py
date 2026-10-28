"""Internal services shared by plant API views."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from django.core.files.uploadedfile import UploadedFile
from django.db import IntegrityError
from wagtail.images.models import Image
from wagtail.models import Collection as WagtailCollection

from .models import Collection, PlantImage, Species, SpeciesImage


@dataclass(frozen=True)
class ImageAssociationResult:
    """Describe whether an uploaded image and its target relationship were created."""

    image_created: bool
    association_created: bool


class ImageAssociationIntegrityError(IntegrityError):
    """Report a relationship integrity failure after image creation state is known."""

    def __init__(self, image_created: bool) -> None:
        """Initialize the error with the image creation result for legacy responses."""

        super().__init__("Could not create image relationship.")
        self.image_created = image_created


def create_brahms_image_association(
    uploaded_image: UploadedFile,
    target: Union[Collection, Species],
    copyright_text: str,
) -> ImageAssociationResult:
    """Store an upload in BRAHMS Data and attach it to a plant or species.

    Image lookup, tagging, captions, copyright values, and relationship lookup
    intentionally match the established single-record upload endpoints.
    """

    image, image_created = Image.objects.get_or_create(
        title=uploaded_image.name,
        defaults={
            "file": uploaded_image,
            "collection": WagtailCollection.objects.get(name="BRAHMS Data"),
        },
    )
    if image_created:
        image.tags.add("BRAHMS")

    try:
        association_created = associate_brahms_image(image, target, copyright_text)
    except IntegrityError as error:
        raise ImageAssociationIntegrityError(image_created) from error

    return ImageAssociationResult(
        image_created=image_created,
        association_created=association_created,
    )


def associate_brahms_image(
    image: Image,
    target: Union[Collection, Species],
    copyright_text: str,
) -> bool:
    """Attach an existing Wagtail image with the established BRAHMS semantics."""

    if isinstance(target, Species):
        _, association_created = SpeciesImage.objects.get_or_create(
            species=target,
            image=image,
            copyright=copyright_text,
            defaults={"caption": target.full_name},
        )
    else:
        _, association_created = PlantImage.objects.get_or_create(
            collection=target,
            image=image,
            copyright=copyright_text,
            defaults={"caption": target.species.full_name},
        )

    return association_created

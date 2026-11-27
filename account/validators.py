from pathlib import Path
from PIL import Image, UnidentifiedImageError
from django.core.exceptions import ValidationError

MAX_PROFILE_PICTURE_SIZE = 2 * 1024 * 1024  # 2 MB
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
ALLOWED_IMAGE_FORMATS = {'JPEG', 'PNG', 'WEBP'}


def validate_profile_picture(file_obj) -> None:
    if file_obj.size > MAX_PROFILE_PICTURE_SIZE:
        raise ValidationError('Profile picture size must not exceed 2 MB.')

    ext = Path(file_obj.name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError('Unsupported file extension. Allowed: JPG, JPEG, PNG, WEBP.')

    try:
        file_obj.seek(0)
        with Image.open(file_obj) as img:
            img.verify()
            if img.format not in ALLOWED_IMAGE_FORMATS:
                raise ValidationError('Invalid image format.')
    except (UnidentifiedImageError, OSError) as exc:
        raise ValidationError('Uploaded file is not a valid image.') from exc
    finally:
        file_obj.seek(0)
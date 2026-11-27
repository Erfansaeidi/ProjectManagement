import zipfile
from io import BytesIO
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from django.core.exceptions import ValidationError

MAX_ATTACHMENT_SIZE = 5 * 1024 * 1024  # 5 MB

ALLOWED_ATTACHMENT_EXTENSIONS = {
    '.pdf',
    '.png',
    '.jpg',
    '.jpeg',
    '.webp',
    '.txt',
    '.csv',
    '.doc',
    '.docx',
}

ALLOWED_IMAGE_FORMATS = {'PNG', 'JPEG', 'WEBP'}
OLE2_HEADER = b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'


def validate_ticket_attachment(file_obj) -> None:
    if file_obj.size == 0:
        raise ValidationError('Uploaded file cannot be empty.')

    if file_obj.size > MAX_ATTACHMENT_SIZE:
        raise ValidationError('Attachment size must not exceed 5 MB.')

    ext = Path(file_obj.name).suffix.lower()
    if ext not in ALLOWED_ATTACHMENT_EXTENSIONS:
        raise ValidationError(
            'Unsupported file type. Allowed formats: PDF, PNG, JPG, JPEG, WEBP, TXT, CSV, DOC, DOCX.'
        )

    try:
        file_obj.seek(0)
        raw_bytes = file_obj.read()
    finally:
        file_obj.seek(0)

    if ext in {'.png', '.jpg', '.jpeg', '.webp'}:
        try:
            with Image.open(BytesIO(raw_bytes)) as img:
                img.verify()
                if img.format not in ALLOWED_IMAGE_FORMATS:
                    raise ValidationError('Invalid image format.')
        except (UnidentifiedImageError, OSError) as exc:
            raise ValidationError('Uploaded file is not a valid image.') from exc
        return

    if ext == '.pdf':
        if not raw_bytes.startswith(b'%PDF-'):
            raise ValidationError('Uploaded file is not a valid PDF document.')
        return

    if ext == '.docx':
        try:
            with zipfile.ZipFile(BytesIO(raw_bytes)) as archive:
                if 'word/document.xml' not in archive.namelist():
                    raise ValidationError('Invalid DOCX file structure.')
        except zipfile.BadZipFile as exc:
            raise ValidationError('Uploaded file is not a valid DOCX document.') from exc
        return

    if ext == '.doc':
        if not raw_bytes.startswith(OLE2_HEADER):
            raise ValidationError('Uploaded file is not a valid DOC document.')
        return

    if ext in {'.txt', '.csv'}:
        if b'\x00' in raw_bytes:
            raise ValidationError('Binary content is not allowed in text files.')
        try:
            raw_bytes.decode('utf-8')
        except UnicodeDecodeError as exc:
            raise ValidationError('Text files must be valid UTF-8.') from exc
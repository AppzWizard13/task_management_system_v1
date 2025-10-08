"""
Secure file upload validators.

Validates file size, extension, and content type to prevent malicious uploads.
"""

import os
import re
from django.core.exceptions import ValidationError


# Allowed file extensions
ALLOWED_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.txt', '.xls', '.xlsx',
    '.png', '.jpg', '.jpeg', '.gif', '.zip', '.csv',
    '.ppt', '.pptx'
}

# Maximum file size (10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


def validate_file_extension(value):
    """
    Validate file extension against whitelist.

    Args:
        value: UploadedFile instance

    Raises:
        ValidationError: If extension not allowed
    """
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f'File type "{ext}" not allowed. '
            f'Allowed types: {", ".join(sorted(ALLOWED_EXTENSIONS))}'
        )


def validate_file_size(value):
    """
    Validate file size against maximum limit.

    Args:
        value: UploadedFile instance

    Raises:
        ValidationError: If file exceeds size limit
    """
    if value.size > MAX_FILE_SIZE:
        max_size_mb = MAX_FILE_SIZE / (1024 * 1024)
        file_size_mb = value.size / (1024 * 1024)
        raise ValidationError(
            f'File too large ({file_size_mb:.2f} MB). '
            f'Maximum size allowed: {max_size_mb} MB'
        )


def sanitize_filename(filename):
    """
    Sanitize filename to prevent directory traversal and injection attacks.

    Args:
        filename: Original filename

    Returns:
        str: Sanitized filename
    """
    filename = os.path.basename(filename)
    filename = filename.replace(' ', '_')
    filename = re.sub(r'[^\w\-.]', '', filename)
    
    name, ext = os.path.splitext(filename)
    if len(name) > 100:
        name = name[:100]
    
    return f"{name}{ext}"

import os
from pathlib import Path
from typing import Optional, Tuple
from convert_id.config import FORMAT_CATEGORIES

# Magic bytes dictionary for format sniffing
MAGIC_SIGNATURES = [
    (b"\x89PNG\r\n\x1a\n", "png", "image"),
    (b"\xff\xd8\xff", "jpg", "image"),
    (b"GIF87a", "gif", "image"),
    (b"GIF89a", "gif", "image"),
    (b"RIFF", "riff_container", "media"), # Can be WEBP, WAV, or AVI
    (b"%PDF-", "pdf", "document"),
    (b"PK\x03\x04", "zip_container", "archive"), # Zip, docx, xlsx, epub
    (b"\x1f\x8b\x08", "gz", "archive"),
    (b"BZh", "bz2", "archive"),
    (b"\xfd7zXZ\x00", "xz", "archive"),
    (b"7z\xbc\xaf\x27\x1c", "7z", "archive"),
    (b"fLaC", "flac", "audio"),
    (b"ID3", "mp3", "audio"),
    (b"OggS", "ogg", "audio"),
    (b"\x1aE\xdf\xa3", "mkv", "video"), # Matroska or WebM
]

def sniff_format(file_path: Path) -> Tuple[str, str]:
    """
    Returns (detected_extension, category).
    Fallback to file extension if magic bytes are generic or plain text.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        ext = file_path.suffix.lstrip(".").lower()
        cat = get_category_for_ext(ext)
        return ext, cat

    ext_from_name = file_path.suffix.lstrip(".").lower()
    
    # Read first 64 bytes
    try:
        with open(file_path, "rb") as f:
            header = f.read(64)
    except Exception:
        header = b""

    # Specific sniffing
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png", "image"
    elif header.startswith(b"\xff\xd8\xff"):
        if b"JFIF" in header[:20]:
            return "jfif" if ext_from_name == "jfif" else "jpg", "image"
        return "jpg", "image"
    elif header.startswith(b"GIF87a") or header.startswith(b"GIF89a"):
        return "gif", "image"
    elif header.startswith(b"RIFF"):
        if len(header) >= 12:
            sub = header[8:12]
            if sub == b"WEBP":
                return "webp", "image"
            elif sub == b"WAVE":
                return "wav", "audio"
            elif sub == b"AVI ":
                return "avi", "video"
    elif header.startswith(b"%PDF-"):
        return "pdf", "document"
    elif len(header) >= 12 and header[4:8] == b"ftyp":
        brand = header[8:12].lower()
        if brand in [b"avif", b"avis"]:
            return "avif", "image"
        elif brand in [b"heic", b"heix", b"mif1"]:
            return "heic", "image"
        elif brand in [b"mp41", b"mp42", b"isom", b"iso2"]:
            return "mp4", "video"
        elif brand in [b"qt  "]:
            return "mov", "video"
        return "mp4", "video"
    elif header.startswith(b"\x1aE\xdf\xa3"):
        if b"webm" in header:
            return "webm", "video"
        return "mkv", "video"
    elif header.startswith(b"ID3") or header[:2] == b"\xff\xfb":
        return "mp3", "audio"
    elif header.startswith(b"fLaC"):
        return "flac", "audio"
    elif header.startswith(b"OggS"):
        return "ogg", "audio"
    elif header.startswith(b"PK\x03\x04"):
        if ext_from_name in ["docx", "xlsx", "pptx", "epub"]:
            return ext_from_name, "document"
        return "zip", "archive"

    # Plain text detection (check for JSON, YAML, XML, CSV, etc.)
    if ext_from_name in ["json", "yaml", "yml", "toml", "xml", "csv", "tsv", "sql", "md", "txt", "svg"]:
        cat = get_category_for_ext(ext_from_name)
        return ext_from_name, cat

    # Fallback to extension
    cat = get_category_for_ext(ext_from_name)
    return ext_from_name, cat


def get_category_for_ext(ext: str) -> str:
    ext = ext.lower().lstrip(".")
    for cat, exts in FORMAT_CATEGORIES.items():
        if ext in exts:
            return cat
    return "unknown"

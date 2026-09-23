import os
import sys
from pathlib import Path

# Base App Directory
APP_DIR = Path.home() / ".convertid"
APP_DIR.mkdir(parents=True, exist_ok=True)

BIN_DIR = APP_DIR / "bin"
BIN_DIR.mkdir(parents=True, exist_ok=True)

TEMP_DIR = APP_DIR / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_DIR = APP_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HOTFOLDER_DIR = APP_DIR / "hotfolder"
HOTFOLDER_DIR.mkdir(parents=True, exist_ok=True)

# Add BIN_DIR to PATH dynamically
bin_str = str(BIN_DIR)
if bin_str not in os.environ.get("PATH", ""):
    os.environ["PATH"] = bin_str + os.pathsep + os.environ.get("PATH", "")

# Platform
IS_WINDOWS = sys.platform == "win32"
IS_MACOS = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")

# Supported Format Matrix (Input & Output)
FORMAT_CATEGORIES = {
    "image": [
        "png", "jpg", "jpeg", "jfif", "webp", "avif", "bmp", "tiff", "tif", 
        "gif", "ico", "svg", "eps", "tga", "dds"
    ],
    "video": [
        "mp4", "mkv", "avi", "mov", "webm", "flv", "wmv", "ts", "m4v", "gif"
    ],
    "audio": [
        "mp3", "wav", "flac", "aac", "ogg", "m4a", "opus", "wma", "aiff"
    ],
    "document": [
        "pdf", "docx", "doc", "txt", "md", "markdown", "html", "htm", "epub", "rtf"
    ],
    "data": [
        "json", "yaml", "yml", "toml", "xml", "csv", "tsv", "sql", "xlsx", "xls", "parquet"
    ],
    "archive": [
        "zip", "tar", "gz", "tar.gz", "tgz", "bz2", "tar.bz2", "xz", "tar.xz", "7z"
    ],
    "code": [
        "svg_to_react", "svg_to_vue", "svg_to_flutter"
    ]
}

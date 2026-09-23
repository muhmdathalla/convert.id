import os
import sys
import shutil
import zipfile
import tarfile
import urllib.request
from pathlib import Path
from typing import Optional, Dict
from convert_id.config import BIN_DIR, IS_WINDOWS, IS_MACOS, IS_LINUX

FFMPEG_URLS = {
    "win32": "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
    "darwin": "https://evermeet.cx/ffmpeg/getrelease/zip",
    "linux": "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
}

def find_binary(binary_name: str) -> Optional[Path]:
    """
    Search for binary in:
    1. convert.id local bin dir (~/.convertid/bin)
    2. System PATH
    """
    suffix = ".exe" if IS_WINDOWS else ""
    local_path = BIN_DIR / f"{binary_name}{suffix}"
    if local_path.exists() and os.access(local_path, os.X_OK if not IS_WINDOWS else os.R_OK):
        return local_path
    
    # Check in subdirectories of BIN_DIR (e.g. ffmpeg-xxx/bin/)
    for p in BIN_DIR.glob(f"**/{binary_name}{suffix}"):
        if p.is_file():
            return p

    # Check system PATH
    sys_path = shutil.which(binary_name)
    if sys_path:
        return Path(sys_path)

    return None

def get_ffmpeg_path() -> Optional[Path]:
    return find_binary("ffmpeg")

def get_ffprobe_path() -> Optional[Path]:
    return find_binary("ffprobe")

def check_dependencies() -> Dict[str, Dict]:
    """
    Returns status of all external engine tools.
    """
    ffmpeg_p = get_ffmpeg_path()
    ffprobe_p = get_ffprobe_path()
    
    return {
        "ffmpeg": {
            "name": "FFmpeg (Video/Audio Engine)",
            "installed": ffmpeg_p is not None,
            "path": str(ffmpeg_p) if ffmpeg_p else None,
            "required_for": ["Video conversion", "Audio conversion", "Silence detection", "LUFS normalizer"]
        },
        "ffprobe": {
            "name": "FFprobe (Media Inspector)",
            "installed": ffprobe_p is not None,
            "path": str(ffprobe_p) if ffprobe_p else None,
            "required_for": ["Detailed codec & bitrate analysis", "Target size calculation"]
        },
        "pillow": {
            "name": "Pillow (Image Engine)",
            "installed": True,
            "path": "Python Built-in",
            "required_for": ["PNG, JPG, JFIF, WEBP, AVIF, TIFF, BMP, ICO, EXIF"]
        },
        "pypdf": {
            "name": "PyPDF (Document Engine)",
            "installed": True,
            "path": "Python Built-in",
            "required_for": ["PDF merger, splitter, unlock, auto-redact, compress"]
        },
        "opencv": {
            "name": "OpenCV (Computer Vision)",
            "installed": True,
            "path": "Python Built-in",
            "required_for": ["Pixel diff, background segmentation, frame extraction"]
        }
    }

def install_portable_ffmpeg(progress_callback=None) -> bool:
    """
    Download and extract portable ffmpeg to ~/.convertid/bin
    """
    plat = sys.platform
    url = FFMPEG_URLS.get(plat)
    if not url:
        return False
    
    archive_ext = ".zip" if (IS_WINDOWS or IS_MACOS) else ".tar.xz"
    download_path = BIN_DIR / f"ffmpeg_download{archive_ext}"
    
    try:
        def reporthook(blocknum, blocksize, totalsize):
            if totalsize > 0 and progress_callback:
                percent = min(100, int(blocknum * blocksize * 100 / totalsize))
                progress_callback(percent, f"Downloading FFmpeg... {percent}%")

        urllib.request.urlretrieve(url, download_path, reporthook=reporthook)

        if archive_ext == ".zip":
            with zipfile.ZipFile(download_path, 'r') as zip_ref:
                for member in zip_ref.namelist():
                    filename = os.path.basename(member)
                    if filename in ["ffmpeg.exe", "ffprobe.exe", "ffmpeg", "ffprobe"]:
                        source = zip_ref.open(member)
                        target = open(BIN_DIR / filename, "wb")
                        with source, target:
                            shutil.copyfileobj(source, target)
                        if not IS_WINDOWS:
                            os.chmod(BIN_DIR / filename, 0o755)
        elif archive_ext.endswith(".tar.xz"):
            with tarfile.open(download_path, "r:xz") as tar:
                for member in tar.getmembers():
                    filename = os.path.basename(member.name)
                    if filename in ["ffmpeg", "ffprobe"]:
                        f = tar.extractfile(member)
                        if f:
                            target = open(BIN_DIR / filename, "wb")
                            with f, target:
                                shutil.copyfileobj(f, target)
                            os.chmod(BIN_DIR / filename, 0o755)

        if download_path.exists():
            download_path.unlink()
        return True
    except Exception as e:
        if progress_callback:
            progress_callback(-1, f"Failed to download FFmpeg: {e}")
        return False

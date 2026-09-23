from pathlib import Path
from typing import Optional, List, Dict, Any

from convert_id.engines.base import BaseEngine, ConversionResult
from convert_id.engines.image_engine import ImageEngine
from convert_id.engines.video_engine import VideoEngine
from convert_id.engines.audio_engine import AudioEngine
from convert_id.engines.doc_engine import DocEngine
from convert_id.engines.data_engine import DataEngine
from convert_id.engines.archive_engine import ArchiveEngine
from convert_id.engines.code_engine import CodeEngine
from convert_id.utils.format_detector import sniff_format

ENGINES: List[BaseEngine] = [
    ImageEngine(),
    VideoEngine(),
    AudioEngine(),
    DocEngine(),
    DataEngine(),
    ArchiveEngine(),
    CodeEngine(),
]

def get_engine(input_ext: str, output_ext: str) -> Optional[BaseEngine]:
    """Finds matching engine for input -> output conversion."""
    in_e = input_ext.lower().lstrip(".")
    out_e = output_ext.lower().lstrip(".")
    for engine in ENGINES:
        if engine.can_handle(in_e, out_e):
            return engine
    return None

def convert_file(input_file: Path, output_file_or_ext: str, **kwargs) -> ConversionResult:
    """
    Central convert dispatch:
    - Automatically sniffs real format
    - Resolves output path
    - Delegates to appropriate engine
    """
    input_path = Path(input_file)
    if not input_path.exists():
        return ConversionResult(
            success=False,
            output_path=None,
            original_size=0,
            converted_size=0,
            format_from="",
            format_to="",
            message=f"Source file does not exist: {input_path}"
        )

    in_ext, _ = sniff_format(input_path)

    # Determine target output path
    out_str = str(output_file_or_ext)
    if "." in out_str and not out_str.startswith("."):
        out_path = Path(out_str)
        out_ext = out_path.suffix.lstrip(".").lower()
    else:
        out_ext = out_str.lstrip(".").lower()
        out_path = input_path.with_suffix(f".{out_ext}")

    engine = get_engine(in_ext, out_ext)
    if not engine:
        return ConversionResult(
            success=False,
            output_path=None,
            original_size=input_path.stat().st_size,
            converted_size=0,
            format_from=in_ext,
            format_to=out_ext,
            message=f"No engine registered to convert {in_ext.upper()} to {out_ext.upper()}."
        )

    return engine.convert(input_path, out_path, **kwargs)

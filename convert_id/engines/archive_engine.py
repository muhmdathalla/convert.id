import io
import os
import tarfile
import zipfile
from pathlib import Path
from typing import Optional, List, Dict, Any

from convert_id.engines.base import BaseEngine, ConversionResult

class ArchiveEngine(BaseEngine):
    name = "ArchiveEngine"
    supported_inputs = ["zip", "tar", "gz", "tar.gz", "tgz", "bz2", "tar.bz2", "xz", "tar.xz"]
    supported_outputs = ["zip", "tar", "tar.gz", "tar.bz2", "tar.xz"]

    def convert(self, input_path: Path, output_path: Path, **kwargs) -> ConversionResult:
        input_path = Path(input_path)
        output_path = Path(output_path)
        orig_size = input_path.stat().st_size if input_path.exists() else 0
        in_name = input_path.name.lower()
        out_name = output_path.name.lower()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Read files from source archive
            files_map = {} # filename -> bytes

            if in_name.endswith(".zip"):
                with zipfile.ZipFile(input_path, "r") as zf:
                    for item in zf.infolist():
                        if not item.is_dir():
                            files_map[item.filename] = zf.read(item.filename)
            elif any(in_name.endswith(ext) for ext in [".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tar.xz"]):
                mode = "r:*"
                with tarfile.open(input_path, mode) as tf:
                    for member in tf.getmembers():
                        if member.isfile():
                            f = tf.extractfile(member)
                            if f:
                                files_map[member.name] = f.read()

            if not files_map:
                return ConversionResult(
                    success=False,
                    output_path=None,
                    original_size=orig_size,
                    converted_size=0,
                    format_from=input_path.suffix.lstrip("."),
                    format_to=output_path.suffix.lstrip("."),
                    message="Archive was empty or format unsupported."
                )

            # Write to target archive format
            if out_name.endswith(".zip"):
                with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
                    for name, data in files_map.items():
                        zf.writestr(name, data)
            else:
                tar_mode = "w"
                if out_name.endswith(".tar.gz") or out_name.endswith(".tgz"):
                    tar_mode = "w:gz"
                elif out_name.endswith(".tar.bz2"):
                    tar_mode = "w:bz2"
                elif out_name.endswith(".tar.xz"):
                    tar_mode = "w:xz"

                with tarfile.open(output_path, tar_mode) as tf:
                    for name, data in files_map.items():
                        ti = tarfile.TarInfo(name=name)
                        ti.size = len(data)
                        tf.addfile(ti, io.BytesIO(data))

            new_sz = output_path.stat().st_size
            return ConversionResult(
                success=True,
                output_path=output_path,
                original_size=orig_size,
                converted_size=new_sz,
                format_from=input_path.suffix.lstrip("."),
                format_to=output_path.suffix.lstrip("."),
                message=f"Repacked {len(files_map)} files into {output_path.name} on the fly."
            )

        except Exception as e:
            return ConversionResult(
                success=False,
                output_path=None,
                original_size=orig_size,
                converted_size=0,
                format_from=input_path.suffix.lstrip("."),
                format_to=output_path.suffix.lstrip("."),
                message=f"Archive repack failed: {str(e)}"
            )

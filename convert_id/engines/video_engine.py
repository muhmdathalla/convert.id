import os
import subprocess
import json
import math
from pathlib import Path
from typing import Optional, Dict, Any, List

from convert_id.engines.base import BaseEngine, ConversionResult
from convert_id.utils.binary_manager import get_ffmpeg_path, get_ffprobe_path

class VideoEngine(BaseEngine):
    name = "VideoEngine"
    supported_inputs = ["mp4", "mkv", "avi", "mov", "webm", "flv", "wmv", "ts", "m4v", "gif"]
    supported_outputs = ["mp4", "mkv", "avi", "mov", "webm", "gif", "mp3", "wav", "aac"]

    def convert(self, input_path: Path, output_path: Path, **kwargs) -> ConversionResult:
        ffmpeg_bin = get_ffmpeg_path()
        if not ffmpeg_bin:
            return ConversionResult(
                success=False,
                output_path=None,
                original_size=input_path.stat().st_size if input_path.exists() else 0,
                converted_size=0,
                format_from=input_path.suffix.lstrip("."),
                format_to=output_path.suffix.lstrip("."),
                message="FFmpeg is not installed. Run 'convert doctor' to auto-install portable FFmpeg."
            )

        input_path = Path(input_path)
        output_path = Path(output_path)
        orig_size = input_path.stat().st_size if input_path.exists() else 0
        in_ext = input_path.suffix.lstrip(".").lower()
        out_ext = output_path.suffix.lstrip(".").lower()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 1. Feature: Spritesheet Generator
        if kwargs.get("spritesheet", False):
            return self._generate_spritesheet(input_path, output_path, ffmpeg_bin, orig_size, in_ext, out_ext, **kwargs)

        # 2. Feature: Faststart / Container Repair
        if kwargs.get("repair_container", False):
            cmd = [
                str(ffmpeg_bin), "-y", "-err_detect", "ignore_err",
                "-i", str(input_path),
                "-c", "copy", "-movflags", "+faststart",
                str(output_path)
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            new_sz = output_path.stat().st_size if output_path.exists() else 0
            return ConversionResult(
                success=output_path.exists() and new_sz > 0,
                output_path=output_path,
                original_size=orig_size,
                converted_size=new_sz,
                format_from=in_ext,
                format_to=out_ext,
                message="Repaired video container and moved moov atom to start."
            )

        # 3. Feature: Video to High-Quality GIF / Animated WebP
        if out_ext == "gif":
            fps = kwargs.get("fps", 15)
            scale = kwargs.get("scale", 480)
            vf = f"fps={fps},scale={scale}:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer"
            cmd = [
                str(ffmpeg_bin), "-y", "-i", str(input_path),
                "-vf", vf,
                str(output_path)
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            new_sz = output_path.stat().st_size if output_path.exists() else 0
            return ConversionResult(
                success=output_path.exists() and new_sz > 0,
                output_path=output_path,
                original_size=orig_size,
                converted_size=new_sz,
                format_from=in_ext,
                format_to=out_ext,
                message="Converted video to high-fidelity palette-optimized GIF."
            )

        # 4. Feature: Extract Audio
        if out_ext in ["mp3", "wav", "aac", "flac"]:
            cmd = [
                str(ffmpeg_bin), "-y", "-i", str(input_path),
                "-vn", "-q:a", "2",
                str(output_path)
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            new_sz = output_path.stat().st_size if output_path.exists() else 0
            return ConversionResult(
                success=output_path.exists() and new_sz > 0,
                output_path=output_path,
                original_size=orig_size,
                converted_size=new_sz,
                format_from=in_ext,
                format_to=out_ext,
                message=f"Extracted audio track to {out_ext.upper()}."
            )

        # 5. Feature: Target Size Budget (2-pass calculation)
        target_bytes = kwargs.get("target_size_bytes")
        if target_bytes:
            duration = self._get_duration(input_path)
            if duration and duration > 0:
                # 8 bits per byte, subtract 128kbps audio
                total_kbits = (target_bytes * 8) / 1000
                total_kbps = total_kbits / duration
                audio_kbps = min(128, int(total_kbps * 0.15))
                video_kbps = max(50, int(total_kbps - audio_kbps))

                # Pass 1
                cmd_p1 = [
                    str(ffmpeg_bin), "-y", "-i", str(input_path),
                    "-c:v", "libx264", "-b:v", f"{video_kbps}k",
                    "-pass", "1", "-an", "-f", "null", os.devnull
                ]
                subprocess.run(cmd_p1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                # Pass 2
                cmd_p2 = [
                    str(ffmpeg_bin), "-y", "-i", str(input_path),
                    "-c:v", "libx264", "-b:v", f"{video_kbps}k",
                    "-pass", "2", "-c:a", "aac", "-b:a", f"{audio_kbps}k",
                    "-movflags", "+faststart",
                    str(output_path)
                ]
                subprocess.run(cmd_p2, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                new_sz = output_path.stat().st_size if output_path.exists() else 0
                return ConversionResult(
                    success=output_path.exists() and new_sz > 0,
                    output_path=output_path,
                    original_size=orig_size,
                    converted_size=new_sz,
                    format_from=in_ext,
                    format_to=out_ext,
                    message=f"Compressed video to target size ({new_sz / 1024 / 1024:.2f} MB)."
                )

        # Standard Video Transcode
        preset = kwargs.get("preset", "medium")
        crf = kwargs.get("crf", "23")
        cmd = [
            str(ffmpeg_bin), "-y", "-i", str(input_path),
            "-c:v", "libx264", "-preset", preset, "-crf", str(crf),
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            str(output_path)
        ]
        
        # Subtitle Hardburn
        subtitle_file = kwargs.get("subtitles")
        if subtitle_file and Path(subtitle_file).exists():
            # Escaping for ffmpeg subtitles filter
            sub_clean = str(Path(subtitle_file)).replace("\\", "/").replace(":", "\\:")
            cmd.insert(cmd.index("-c:v") + 2, "-vf")
            cmd.insert(cmd.index("-vf") + 1, f"subtitles='{sub_clean}'")

        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        new_sz = output_path.stat().st_size if output_path.exists() else 0

        return ConversionResult(
            success=output_path.exists() and new_sz > 0,
            output_path=output_path,
            original_size=orig_size,
            converted_size=new_sz,
            format_from=in_ext,
            format_to=out_ext,
            message="Video converted successfully."
        )

    def _get_duration(self, input_path: Path) -> Optional[float]:
        ffprobe_bin = get_ffprobe_path()
        if not ffprobe_bin:
            return None
        cmd = [
            str(ffprobe_bin), "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(input_path)
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            return float(res.stdout.strip())
        except Exception:
            return None

    def _generate_spritesheet(self, input_path: Path, output_path: Path, ffmpeg_bin: Path, orig_size: int, in_ext: str, out_ext: str, **kwargs) -> ConversionResult:
        """Tile frames into a gaming/web spritesheet atlas."""
        cols = kwargs.get("columns", 5)
        rows = kwargs.get("rows", 5)
        total_frames = cols * rows
        
        duration = self._get_duration(input_path) or 10.0
        fps_rate = total_frames / duration

        vf = f"fps={fps_rate:.4f},scale=160:-1,tile={cols}x{rows}"
        cmd = [
            str(ffmpeg_bin), "-y", "-i", str(input_path),
            "-vf", vf, "-frames:v", "1",
            str(output_path)
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        new_sz = output_path.stat().st_size if output_path.exists() else 0
        return ConversionResult(
            success=output_path.exists() and new_sz > 0,
            output_path=output_path,
            original_size=orig_size,
            converted_size=new_sz,
            format_from=in_ext,
            format_to=out_ext,
            message=f"Generated {cols}x{rows} spritesheet atlas."
        )

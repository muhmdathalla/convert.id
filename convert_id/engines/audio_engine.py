import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

from convert_id.engines.base import BaseEngine, ConversionResult
from convert_id.utils.binary_manager import get_ffmpeg_path

class AudioEngine(BaseEngine):
    name = "AudioEngine"
    supported_inputs = ["mp3", "wav", "flac", "aac", "ogg", "m4a", "opus", "wma", "aiff"]
    supported_outputs = ["mp3", "wav", "flac", "aac", "ogg", "m4a", "opus"]

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

        audio_filters = []

        # 1. Feature: LUFS Loudness Broadcast Normalizer (-14 LUFS standard)
        if kwargs.get("normalize_lufs", False):
            target_lufs = kwargs.get("target_lufs", -14.0)
            audio_filters.append(f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11")

        # 2. Feature: Silence & Dead-Air Stripper
        if kwargs.get("strip_silence", False):
            # Remove silence longer than 0.5s below -45dB
            audio_filters.append("silenceremove=stop_periods=-1:stop_duration=0.5:stop_threshold=-45dB:start_periods=1:start_duration=0.2:start_threshold=-45dB")

        # 3. Codec & Bitrate mappings
        cmd = [str(ffmpeg_bin), "-y", "-i", str(input_path)]

        if audio_filters:
            cmd.extend(["-af", ",".join(audio_filters)])

        if out_ext == "mp3":
            cmd.extend(["-c:a", "libmp3lame", "-b:a", kwargs.get("bitrate", "320k")])
        elif out_ext == "wav":
            cmd.extend(["-c:a", "pcm_s16le"])
        elif out_ext == "flac":
            cmd.extend(["-c:a", "flac"])
        elif out_ext == "aac" or out_ext == "m4a":
            cmd.extend(["-c:a", "aac", "-b:a", kwargs.get("bitrate", "256k")])
        elif out_ext == "ogg":
            cmd.extend(["-c:a", "libvorbis", "-q:a", "6"])
        elif out_ext == "opus":
            cmd.extend(["-c:a", "libopus", "-b:a", "128k"])

        cmd.append(str(output_path))
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        new_sz = output_path.stat().st_size if output_path.exists() else 0
        return ConversionResult(
            success=output_path.exists() and new_sz > 0,
            output_path=output_path,
            original_size=orig_size,
            converted_size=new_sz,
            format_from=in_ext,
            format_to=out_ext,
            message="Audio converted and processed successfully."
        )

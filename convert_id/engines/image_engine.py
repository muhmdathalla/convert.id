import os
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any
from PIL import Image, ImageOps

from convert_id.engines.base import BaseEngine, ConversionResult
from convert_id.utils.vectorizer import raster_to_svg
from convert_id.utils.stego import hide_payload_in_image, extract_payload_from_image

class ImageEngine(BaseEngine):
    name = "ImageEngine"
    supported_inputs = [
        "png", "jpg", "jpeg", "jfif", "webp", "avif", "bmp", "tiff", "tif", 
        "gif", "ico", "svg", "tga", "dds"
    ]
    supported_outputs = [
        "png", "jpg", "jpeg", "jfif", "webp", "avif", "bmp", "tiff", "tif", 
        "gif", "ico", "svg"
    ]

    def convert(self, input_path: Path, output_path: Path, **kwargs) -> ConversionResult:
        input_path = Path(input_path)
        output_path = Path(output_path)
        orig_size = input_path.stat().st_size if input_path.exists() else 0
        
        in_ext = input_path.suffix.lstrip(".").lower()
        out_ext = output_path.suffix.lstrip(".").lower()
        
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 1. Special Feature: Raster to true SVG
        if out_ext == "svg" and in_ext != "svg":
            color_mode = kwargs.get("vector_mode", "monochrome")
            raster_to_svg(input_path, output_path, color_mode=color_mode)
            new_size = output_path.stat().st_size
            return ConversionResult(
                success=True,
                output_path=output_path,
                original_size=orig_size,
                converted_size=new_size,
                format_from=in_ext,
                format_to=out_ext,
                message="Vectorized raster to true SVG paths."
            )

        # Open image
        img = Image.open(input_path)

        # 2. Feature: Background Removal / Transparent Mask (Offline GrabCut or Chroma/Threshold)
        if kwargs.get("remove_bg", False):
            img = self._remove_background(img)

        # 3. Feature: EXIF Stripping / Phantom Scrub
        strip_exif = kwargs.get("strip_exif", True)
        if strip_exif:
            # Recreate clean data without exif tags
            data = list(img.getdata())
            clean_img = Image.new(img.mode, img.size)
            clean_img.putdata(data)
            img = clean_img

        # 4. Feature: Watermarking
        watermark_text = kwargs.get("watermark")
        if watermark_text:
            # We can stamp watermark or overlay
            pass

        # Handle color modes
        target_format = out_ext.upper()
        if target_format in ["JPG", "JPEG", "JFIF"]:
            target_format = "JPEG"
            if img.mode in ("RGBA", "P", "LA"):
                # Fill transparent with white or background color
                bg = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "RGBA":
                    bg.paste(img, mask=img.split()[3])
                else:
                    bg.paste(img.convert("RGBA"))
                img = bg
            elif img.mode != "RGB":
                img = img.convert("RGB")
        elif target_format == "ICO":
            # Resize to icon sizes
            sizes = kwargs.get("ico_sizes", [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
            img.save(output_path, format="ICO", sizes=sizes)
            new_size = output_path.stat().st_size
            return ConversionResult(
                success=True,
                output_path=output_path,
                original_size=orig_size,
                converted_size=new_size,
                format_from=in_ext,
                format_to=out_ext,
                message="Generated multi-resolution ICO icon."
            )

        # 5. Feature: Target Size Budget Fitting
        target_size_bytes = kwargs.get("target_size_bytes")
        if target_size_bytes and target_format in ["JPEG", "WEBP"]:
            self._save_to_budget(img, output_path, target_format, target_size_bytes)
        else:
            quality = kwargs.get("quality", 92)
            optimize = kwargs.get("optimize", True)
            save_kwargs = {}
            if target_format in ["JPEG", "WEBP"]:
                save_kwargs["quality"] = quality
                save_kwargs["optimize"] = optimize
            elif target_format == "PNG":
                save_kwargs["optimize"] = optimize
                
            img.save(output_path, format=target_format, **save_kwargs)

        new_size = output_path.stat().st_size
        return ConversionResult(
            success=True,
            output_path=output_path,
            original_size=orig_size,
            converted_size=new_size,
            format_from=in_ext,
            format_to=out_ext,
            message="Image successfully converted."
        )

    def _save_to_budget(self, img: Image.Image, output_path: Path, fmt: str, target_bytes: int):
        """Binary search quality and scale to fit strict budget."""
        low_q, high_q = 5, 95
        best_quality = 50
        current_img = img.copy()

        for _ in range(6):
            mid_q = (low_q + high_q) // 2
            current_img.save(output_path, format=fmt, quality=mid_q, optimize=True)
            sz = output_path.stat().st_size
            if sz <= target_bytes:
                best_quality = mid_q
                low_q = mid_q + 1
            else:
                high_q = mid_q - 1

        # If even at low quality it exceeds, scale dimensions down
        sz = output_path.stat().st_size
        while sz > target_bytes and (current_img.width > 200 and current_img.height > 200):
            new_w = int(current_img.width * 0.85)
            new_h = int(current_img.height * 0.85)
            current_img = current_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            current_img.save(output_path, format=fmt, quality=best_quality, optimize=True)
            sz = output_path.stat().st_size

    def _remove_background(self, img: Image.Image) -> Image.Image:
        """Removes background using GrabCut or thresholding without external cloud."""
        rgba = img.convert("RGBA")
        cv_img = cv2.cvtColor(np.array(rgba), cv2.COLOR_RGBA2BGR)
        h, w = cv_img.shape[:2]

        mask = np.zeros((h, w), np.uint8)
        bgdModel = np.zeros((1, 65), np.float64)
        fgdModel = np.zeros((1, 65), np.float64)

        # Rectangle margin
        margin_x = max(2, int(w * 0.05))
        margin_y = max(2, int(h * 0.05))
        rect = (margin_x, margin_y, w - 2 * margin_x, h - 2 * margin_y)

        try:
            cv2.grabCut(cv_img, mask, rect, bgdModel, fgdModel, 3, cv2.GC_INIT_WITH_RECT)
            mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
            alpha = (mask2 * 255).astype(np.uint8)
            r, g, b, _ = rgba.split()
            a_channel = Image.fromarray(alpha)
            return Image.merge("RGBA", (r, g, b, a_channel))
        except Exception:
            return rgba

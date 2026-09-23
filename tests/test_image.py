import os
from pathlib import Path
from PIL import Image
from convert_id.engines.image_engine import ImageEngine
from convert_id.utils.vectorizer import raster_to_svg

def test_image_conversions(tmp_path: Path):
    engine = ImageEngine()
    
    # 1. Create a dummy image
    test_img = tmp_path / "sample.jfif"
    img = Image.new("RGB", (200, 200), color=(73, 109, 137))
    img.save(test_img, format="JPEG")

    # 2. Convert JFIF -> PNG
    out_png = tmp_path / "sample.png"
    res1 = engine.convert(test_img, out_png)
    assert res1.success
    assert out_png.exists()
    assert res1.format_to == "png"

    # 3. Convert PNG -> WEBP with quality
    out_webp = tmp_path / "sample.webp"
    res2 = engine.convert(out_png, out_webp, quality=80)
    assert res2.success
    assert out_webp.exists()

    # 4. Raster -> SVG Vectorization
    out_svg = tmp_path / "sample.svg"
    res3 = engine.convert(out_png, out_svg, vector_mode="monochrome")
    assert res3.success
    assert out_svg.exists()
    content = out_svg.read_text(encoding="utf-8")
    assert "<svg" in content
    assert "<path" in content

    print("Image engine test passed successfully!")

if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        test_image_conversions(Path(td))

import tempfile
from pathlib import Path
from convert_id.engines.code_engine import CodeEngine

def test_code_engine():
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        engine = CodeEngine()

        svg_file = tdp / "arrow_icon.svg"
        svg_file.write_text('<svg viewBox="0 0 24 24"><path d="M5 12h14" /></svg>', encoding="utf-8")

        # SVG -> React TSX
        tsx_file = tdp / "ArrowIcon.tsx"
        res = engine.convert(svg_file, tsx_file)
        assert res.success
        assert tsx_file.exists()
        code = tsx_file.read_text(encoding="utf-8")
        assert "export const ArrowIcon" in code
        assert "React.FC<ArrowIconProps>" in code

        print("Code engine test passed successfully!")

if __name__ == "__main__":
    test_code_engine()

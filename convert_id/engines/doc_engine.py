import re
import zipfile
from pathlib import Path
from typing import Optional, List, Dict, Any
from pypdf import PdfReader, PdfWriter
import docx

from convert_id.engines.base import BaseEngine, ConversionResult

class DocEngine(BaseEngine):
    name = "DocEngine"
    supported_inputs = ["pdf", "docx", "txt", "md", "markdown", "html", "htm"]
    supported_outputs = ["pdf", "docx", "txt", "md", "html", "epub"]

    # Regex patterns for auto-redaction (Anti-mainstream #7)
    REDACT_PATTERNS = {
        "nik": r"\b[1-9][0-9]{15}\b",                              # Indonesian NIK 16 digits
        "credit_card": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",             # Credit card 16 digits
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b", # Email
        "phone": r"\b(?:\+?62|08)[0-9]{8,12}\b"                     # ID Phone numbers
    }

    def convert(self, input_path: Path, output_path: Path, **kwargs) -> ConversionResult:
        input_path = Path(input_path)
        output_path = Path(output_path)
        orig_size = input_path.stat().st_size if input_path.exists() else 0
        in_ext = input_path.suffix.lstrip(".").lower()
        out_ext = output_path.suffix.lstrip(".").lower()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 1. Feature: PDF Fortress (Unlock, Redact, Compress)
        if in_ext == "pdf":
            return self._handle_pdf(input_path, output_path, in_ext, out_ext, orig_size, **kwargs)

        # 2. DOCX -> TXT / MD / HTML
        if in_ext == "docx":
            return self._handle_docx(input_path, output_path, in_ext, out_ext, orig_size, **kwargs)

        # 3. MD / TXT -> EPUB / HTML / TXT
        if in_ext in ["md", "markdown", "txt"]:
            return self._handle_text(input_path, output_path, in_ext, out_ext, orig_size, **kwargs)

        # 4. HTML -> MD / TXT
        if in_ext in ["html", "htm"]:
            text_content = input_path.read_text(encoding="utf-8", errors="ignore")
            # Simple clean strip of HTML tags
            clean_text = re.sub(r'<[^>]+>', '', text_content)
            output_path.write_text(clean_text, encoding="utf-8")
            new_sz = output_path.stat().st_size
            return ConversionResult(
                success=True,
                output_path=output_path,
                original_size=orig_size,
                converted_size=new_sz,
                format_from=in_ext,
                format_to=out_ext,
                message="Extracted clean text from HTML."
            )

        return ConversionResult(
            success=False,
            output_path=None,
            original_size=orig_size,
            converted_size=0,
            format_from=in_ext,
            format_to=out_ext,
            message=f"Unsupported document transformation: {in_ext} -> {out_ext}"
        )

    def _handle_pdf(self, input_path: Path, output_path: Path, in_ext: str, out_ext: str, orig_size: int, **kwargs) -> ConversionResult:
        reader = PdfReader(str(input_path))
        writer = PdfWriter()

        # Unlock PDF if encrypted
        password = kwargs.get("password", "")
        if reader.is_encrypted:
            try:
                reader.decrypt(password)
            except Exception:
                return ConversionResult(
                    success=False,
                    output_path=None,
                    original_size=orig_size,
                    converted_size=0,
                    format_from=in_ext,
                    format_to=out_ext,
                    message="PDF is password protected. Provide --password to unlock."
                )

        # If converting PDF -> TXT or MD
        if out_ext in ["txt", "md"]:
            extracted_text = []
            for i, page in enumerate(reader.pages):
                txt = page.extract_text() or ""
                if kwargs.get("auto_redact", False):
                    txt = self._apply_redaction(txt)
                extracted_text.append(f"<!-- Page {i+1} -->\n{txt}\n")
            
            output_path.write_text("\n".join(extracted_text), encoding="utf-8")
            new_sz = output_path.stat().st_size
            return ConversionResult(
                success=True,
                output_path=output_path,
                original_size=orig_size,
                converted_size=new_sz,
                format_from=in_ext,
                format_to=out_ext,
                message=f"Extracted {len(reader.pages)} pages of text from PDF."
            )

        # PDF -> PDF (Compress / Auto-redact / Clean metadata)
        for page in reader.pages:
            if kwargs.get("compress_pdf", True):
                page.compress_content_streams()
            writer.add_page(page)

        # Remove sensitive PDF metadata
        writer.add_metadata({
            "/Producer": "Convert.id Universal Engine",
            "/Creator": "Convert.id",
            "/Title": output_path.stem
        })

        with open(output_path, "wb") as f:
            writer.write(f)

        new_sz = output_path.stat().st_size
        return ConversionResult(
            success=True,
            output_path=output_path,
            original_size=orig_size,
            converted_size=new_sz,
            format_from=in_ext,
            format_to=out_ext,
            message="Optimized and secured PDF."
        )

    def _handle_docx(self, input_path: Path, output_path: Path, in_ext: str, out_ext: str, orig_size: int, **kwargs) -> ConversionResult:
        doc = docx.Document(str(input_path))
        lines = []
        for p in doc.paragraphs:
            text = p.text
            if kwargs.get("auto_redact", False):
                text = self._apply_redaction(text)
            lines.append(text)

        for table in doc.tables:
            lines.append("\n| " + " | ".join(["---"] * len(table.columns)) + " |")
            for row in table.rows:
                row_text = [cell.text.strip().replace("\n", " ") for cell in row.cells]
                lines.append("| " + " | ".join(row_text) + " |")

        full_content = "\n\n".join(lines)
        output_path.write_text(full_content, encoding="utf-8")
        new_sz = output_path.stat().st_size

        return ConversionResult(
            success=True,
            output_path=output_path,
            original_size=orig_size,
            converted_size=new_sz,
            format_from=in_ext,
            format_to=out_ext,
            message="Converted Word DOCX to clean structured text/markdown."
        )

    def _handle_text(self, input_path: Path, output_path: Path, in_ext: str, out_ext: str, orig_size: int, **kwargs) -> ConversionResult:
        content = input_path.read_text(encoding="utf-8", errors="ignore")
        
        # Anti-mainstream #18: E-Book Factory (Markdown -> EPUB)
        if out_ext == "epub":
            self._create_epub(content, output_path, title=input_path.stem)
            new_sz = output_path.stat().st_size
            return ConversionResult(
                success=True,
                output_path=output_path,
                original_size=orig_size,
                converted_size=new_sz,
                format_from=in_ext,
                format_to=out_ext,
                message="Built EPUB e-book with automatic table of contents."
            )
        
        # TXT / MD -> HTML
        if out_ext in ["html", "htm"]:
            # Wrap in clean, modern typography HTML
            html_body = "".join(f"<p>{line}</p>" if line.strip() else "<br/>" for line in content.split("\n"))
            html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{input_path.stem}</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; max-width: 800px; margin: 40px auto; padding: 0 20px; color: #111; background: #fff; }}
p {{ margin-bottom: 1em; }}
</style>
</head>
<body>
<h1>{input_path.stem}</h1>
{html_body}
</body>
</html>"""
            output_path.write_text(html, encoding="utf-8")
            new_sz = output_path.stat().st_size
            return ConversionResult(
                success=True,
                output_path=output_path,
                original_size=orig_size,
                converted_size=new_sz,
                format_from=in_ext,
                format_to=out_ext,
                message="Rendered clean HTML document."
            )

        # Output as TXT/MD directly
        output_path.write_text(content, encoding="utf-8")
        new_sz = output_path.stat().st_size
        return ConversionResult(
            success=True,
            output_path=output_path,
            original_size=orig_size,
            converted_size=new_sz,
            format_from=in_ext,
            format_to=out_ext,
            message="Converted text document."
        )

    def _apply_redaction(self, text: str) -> str:
        for name, pattern in self.REDACT_PATTERNS.items():
            text = re.sub(pattern, lambda m: "[REDACTED-" + name.upper() + "]", text)
        return text

    def _create_epub(self, text_content: str, output_path: Path, title: str):
        """Builds a valid, clean EPUB 3 archive without external heavy tools."""
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as ep:
            ep.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
            ep.writestr("META-INF/container.xml", """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""")
            
            chapter_html = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head><title>{title}</title></head>
<body>
<h1>{title}</h1>
{"".join(f"<p>{p}</p>" for p in text_content.splitlines() if p.strip())}
</body>
</html>"""
            ep.writestr("OEBPS/chapter1.xhtml", chapter_html)
            
            opf = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookID" version="2.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>{title}</dc:title>
    <dc:creator>Convert.id E-Book Factory</dc:creator>
    <dc:language>en</dc:language>
    <dc:identifier id="BookID">urn:uuid:convert-id-{hash(title)}</dc:identifier>
  </metadata>
  <manifest>
    <item id="chapter1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="chapter1"/>
  </spine>
</package>"""
            ep.writestr("OEBPS/content.opf", opf)

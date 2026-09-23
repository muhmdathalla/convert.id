import os
import json
import mimetypes
import socket
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Dict, Any

from convert_id.config import APP_DIR, OUTPUT_DIR, TEMP_DIR
from convert_id.engines import convert_file, ENGINES
from convert_id.utils.format_detector import sniff_format
from convert_id.utils.binary_manager import check_dependencies

WEB_DIR = Path(__file__).parent / "static"

class ConvertIdServer(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        
        # API: Status & Doctor
        if parsed.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            status_data = {
                "version": "1.0.0",
                "system": os.name,
                "dependencies": check_dependencies(),
                "engines": [e.name for e in ENGINES]
            }
            self.wfile.write(json.dumps(status_data).encode("utf-8"))
            return

        # API: Download converted output
        if parsed.path.startswith("/api/download/"):
            filename = urllib.parse.unquote(parsed.path.replace("/api/download/", ""))
            file_path = OUTPUT_DIR / filename
            if file_path.exists() and file_path.is_file():
                self.send_response(200)
                mime, _ = mimetypes.guess_type(str(file_path))
                self.send_header("Content-Type", mime or "application/octet-stream")
                self.send_header("Content-Disposition", f'attachment; filename="{file_path.name}"')
                self.send_header("Content-Length", str(file_path.stat().st_size))
                self.end_headers()
                with open(file_path, "rb") as f:
                    self.wfile.write(f.read())
                return
            else:
                self.send_error(404, "File not found")
                return

        # Serve static assets
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/api/convert":
            self._handle_convert_api()
            return

        self.send_error(404, "Unknown endpoint")

    def _handle_convert_api(self):
        try:
            content_type = self.headers.get('Content-Type', '')
            if not content_type.startswith('multipart/form-data'):
                self._send_json({"success": False, "message": "Expected multipart/form-data"}, status=400)
                return

            # Parse multipart form data
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)

            # Extract boundary
            boundary = content_type.split("boundary=")[1].encode()
            parts = body.split(b"--" + boundary)

            file_bytes = None
            filename = "upload.bin"
            form_fields = {}

            for part in parts:
                if not part or part == b"--\r\n" or part == b"--":
                    continue
                header_part, _, data_part = part.partition(b"\r\n\r\n")
                headers_text = header_part.decode("utf-8", errors="ignore")
                
                # Check for file
                if 'filename="' in headers_text:
                    fn_match = [line for line in headers_text.split("\r\n") if 'filename="' in line]
                    if fn_match:
                        raw_fn = fn_match[0].split('filename="')[1].split('"')[0]
                        filename = os.path.basename(raw_fn)
                    # Strip trailing \r\n
                    if data_part.endswith(b"\r\n"):
                        data_part = data_part[:-2]
                    file_bytes = data_part
                else:
                    # Regular field
                    name_match = [line for line in headers_text.split("\r\n") if 'name="' in line]
                    if name_match:
                        field_name = name_match[0].split('name="')[1].split('"')[0]
                        val = data_part.rstrip(b"\r\n").decode("utf-8", errors="ignore")
                        form_fields[field_name] = val

            if not file_bytes:
                self._send_json({"success": False, "message": "No file uploaded"}, status=400)
                return

            # Save incoming file to TEMP_DIR
            temp_input = TEMP_DIR / filename
            with open(temp_input, "wb") as f:
                f.write(file_bytes)

            target_ext = form_fields.get("target_format", "png").lstrip(".")
            output_name = f"{temp_input.stem}_converted.{target_ext}"
            temp_output = OUTPUT_DIR / output_name

            # Collect options
            kwargs = {}
            if form_fields.get("target_size_bytes"):
                try:
                    kwargs["target_size_bytes"] = int(form_fields["target_size_bytes"])
                except Exception:
                    pass
            if form_fields.get("strip_exif") == "true":
                kwargs["strip_exif"] = True
            if form_fields.get("remove_bg") == "true":
                kwargs["remove_bg"] = True
            if form_fields.get("vector_mode"):
                kwargs["vector_mode"] = form_fields["vector_mode"]
            if form_fields.get("normalize_lufs") == "true":
                kwargs["normalize_lufs"] = True
            if form_fields.get("strip_silence") == "true":
                kwargs["strip_silence"] = True
            if form_fields.get("auto_redact") == "true":
                kwargs["auto_redact"] = True
            if form_fields.get("repair_container") == "true":
                kwargs["repair_container"] = True
            if form_fields.get("spritesheet") == "true":
                kwargs["spritesheet"] = True

            # Run conversion
            res = convert_file(temp_input, str(temp_output), **kwargs)

            if res.success:
                resp = {
                    "success": True,
                    "download_url": f"/api/download/{temp_output.name}",
                    "filename": temp_output.name,
                    "original_size": res.original_size,
                    "converted_size": res.converted_size,
                    "compression_ratio": round(res.compression_ratio, 2),
                    "message": res.message
                }
                self._send_json(resp)
            else:
                self._send_json({"success": False, "message": res.message}, status=500)

        except Exception as e:
            self._send_json({"success": False, "message": str(e)}, status=500)

    def _send_json(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))


def start_web_server(port: int = 4040, open_browser: bool = True):
    server = HTTPServer(("0.0.0.0", port), ConvertIdServer)
    url = f"http://localhost:{port}"
    print(f"\n[Convert.id] Monochromatic Web Workbench active at: {url}")
    print("[Convert.id] 100% Offline Local Engine. Press Ctrl+C to stop.\n")

    if open_browser:
        import webbrowser
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nWeb server stopped.")

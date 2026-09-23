import socket
import http.server
import socketserver
import threading
from pathlib import Path
from rich.console import Console

console = Console()

def get_local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't need to actually connect
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def render_ascii_qr(data: str):
    """Generates simple ASCII QR code in console."""
    try:
        # Check if qrcode python library is installed, otherwise provide rich box link
        import qrcode
        qr = qrcode.QRCode(border=1)
        qr.add_data(data)
        qr.make(fit=True)
        matrix = qr.get_matrix()
        
        for row in matrix:
            line = "".join("  " if col else "██" for col in row)
            console.print(f"[white]{line}[/white]")
    except ImportError:
        # Clean terminal fallback
        console.print("[dim](Install 'qrcode' module for terminal ASCII matrix)[/dim]")

def share_file(file_path: Path, port: int = 8089):
    file_path = Path(file_path)
    if not file_path.exists():
        console.print(f"[bold red]File not found:[/bold red] {file_path}")
        return

    ip = get_local_ip()
    url = f"http://{ip}:{port}/{file_path.name}"

    class CustomHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(file_path.parent), **kwargs)
        def log_message(self, format, *args):
            # Suppress default noisy logs
            pass

    console.print(f"\n[bold white]Convert.id Local Offline Transfer Capsule[/bold white]")
    console.print(f"[dim]Serving:[/dim] [bold]{file_path.name}[/bold] [dim]({file_path.stat().st_size} bytes)[/dim]")
    console.print(f"[dim]Direct LAN URL:[/dim] [bold underline white]{url}[/bold underline white]\n")

    render_ascii_qr(url)
    console.print(f"\n[dim]Scan QR code or open link on your phone/laptop (same Wi-Fi). Press Ctrl+C to terminate server.[/dim]\n")

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), CustomHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            console.print("\n[dim]Transfer capsule server terminated.[/dim]")

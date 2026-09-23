import sys
import argparse
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from convert_id.config import APP_DIR, FORMAT_CATEGORIES
from convert_id.engines import convert_file, ENGINES
from convert_id.doctor import run_doctor
from convert_id.daemon import start_watcher
from convert_id.share import share_file
from convert_id.diff import diff_files
from convert_id.web.app import start_web_server
from convert_id.utils.stego import hide_payload_in_image, extract_payload_from_image

console = Console()

def format_bytes(num_bytes: int) -> str:
    if num_bytes == 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} TB"

def parse_size_str(s: str) -> int:
    s = s.strip().upper()
    if s.endswith("MB"):
        return int(float(s[:-2]) * 1024 * 1024)
    elif s.endswith("KB"):
        return int(float(s[:-2]) * 1024)
    elif s.endswith("GB"):
        return int(float(s[:-2]) * 1024 * 1024 * 1024)
    return int(s)

def print_banner():
    banner = """[bold white]   ______                                __     _     __
  / ____/___  ____ _   _____  _____/ /_   (_)___/ /
 / /   / __ \\/ __ \\ | / / _ \\/ ___/ __/  / / __  / 
/ /___/ /_/ / / / / |/ /  __/ /  / /_   / / /_/ /  
\\____/\\____/_/ /_/|___/\\___/_/   \\__/  /_/\\__,_/   [/bold white]
[dim]Universal All-in-One File Conversion Engine & Ecosystem[/dim]"""
    console.print(Panel.fit(banner, border_style="bright_black"))

def list_formats():
    console.print(Panel.fit("[bold white]Convert.id Supported Formats Matrix[/bold white]", border_style="bright_black"))
    table = Table(border_style="bright_black", header_style="bold white", expand=True)
    table.add_column("Category", style="bold white", width=16)
    table.add_column("Formats Handled", style="dim")

    for cat, exts in FORMAT_CATEGORIES.items():
        table.add_row(cat.upper(), ", ".join(exts))

    console.print(table)
    console.print("\n[dim]Convert any format to any format: convert input.ext [output.ext or target_ext][/dim]\n")

def main():
    if len(sys.argv) > 1 and sys.argv[1] in ["--version", "-v"]:
        console.print("[bold white]Convert.id[/bold white] [dim]v1.0.0[/dim]")
        sys.exit(0)

    # Subcommands check
    if len(sys.argv) > 1:
        sub = sys.argv[1].lower()
        if sub == "doctor":
            auto_fix = "--fix" in sys.argv
            run_doctor(auto_fix=auto_fix)
            sys.exit(0)
        elif sub == "formats":
            list_formats()
            sys.exit(0)
        elif sub == "web":
            port = 4040
            for i, arg in enumerate(sys.argv):
                if arg == "--port" and i + 1 < len(sys.argv):
                    port = int(sys.argv[i + 1])
            start_web_server(port=port)
            sys.exit(0)
        elif sub == "watch":
            p = argparse.ArgumentParser(prog="convert watch")
            p.add_argument("folder", nargs="?", default=None, help="Directory to monitor")
            p.add_argument("--to", default="png", help="Target extension")
            p.add_argument("--out", default=None, help="Output destination directory")
            args, _ = p.parse_known_args(sys.argv[2:])
            watch_dir = Path(args.folder) if args.folder else None
            out_dir = Path(args.out) if args.out else None
            start_watcher(watch_dir=watch_dir, target_ext=args.to, output_dir=out_dir)
            sys.exit(0)
        elif sub == "share":
            if len(sys.argv) < 3:
                console.print("[bold red]Usage: convert share <filepath>[/bold red]")
                sys.exit(1)
            share_file(Path(sys.argv[2]))
            sys.exit(0)
        elif sub == "diff":
            if len(sys.argv) < 4:
                console.print("[bold red]Usage: convert diff <file1> <file2>[/bold red]")
                sys.exit(1)
            diff_files(Path(sys.argv[2]), Path(sys.argv[3]))
            sys.exit(0)
        elif sub in ["--help", "-h", "help"]:
            print_banner()
            console.print("""
[bold white]USAGE:[/bold white]
  convert <input_file> [output_file_or_ext] [OPTIONS]
  convert <subcommand> [OPTIONS]

[bold white]SUBCOMMANDS:[/bold white]
  doctor                Check dependencies (FFmpeg, Poppler, etc.)
  doctor --fix          Auto-install missing portable binaries
  web [--port 4040]     Launch Monochromatic Web Workbench UI
  watch [folder] --to   Background hot-folder auto-conversion daemon
  share <file>          Host offline local Wi-Fi transfer capsule with terminal QR code
  diff <file1> <file2>  Compute visual pixel or tabular difference
  formats               Display all supported format categories

[bold white]ANTI-MAINSTREAM POWER OPTIONS:[/bold white]
  --target-size <size>  Strict budget fitting (e.g. '24MB' or '200KB')
  --vector              Trace raster image into genuine scalable SVG curves
  --strip-exif          Purge 100% EXIF, GPS, camera serials, and privacy tags (Default: ON)
  --remove-bg           Offline background cutout to transparent alpha PNG
  --auto-redact         PDF fortress: auto-mask NIK, Credit Cards, Emails
  --normalize-lufs      Normalize audio loudness to Spotify/YouTube standard (-14 LUFS)
  --strip-silence       Clip dead-air pauses from video or audio
  --spritesheet         Compile video frames into 2D gaming spritesheet atlas
  --repair              Repair corrupted MP4 headers / faststart moov atom
  --stego-hide <file>   Invisibly inject secret file into image pixels
  --stego-extract       Extract hidden steganography secret payload
  --password <pwd>      Password for encrypted stego or PDF unlocking
""")
            sys.exit(0)

    # Standard conversion command line parser
    parser = argparse.ArgumentParser(description="Convert.id — Universal Conversion Engine", add_help=False)
    parser.add_argument("input", help="Source file to convert")
    parser.add_argument("output", nargs="?", default=None, help="Target file name or extension (e.g. 'png', 'output.webp')")
    parser.add_argument("--target-size", default=None, help="Target budget size (e.g. '24MB', '200KB')")
    parser.add_argument("--vector", action="store_true", help="Raster to SVG vectorization")
    parser.add_argument("--no-strip-exif", action="store_true", help="Retain original EXIF metadata")
    parser.add_argument("--remove-bg", action="store_true", help="Segment background to alpha")
    parser.add_argument("--auto-redact", action="store_true", help="Redact NIK, Credit Cards, Emails")
    parser.add_argument("--normalize-lufs", action="store_true", help="Normalize audio to -14 LUFS")
    parser.add_argument("--strip-silence", action="store_true", help="Strip audio/video silence")
    parser.add_argument("--spritesheet", action="store_true", help="Generate 2D gaming spritesheet")
    parser.add_argument("--repair", action="store_true", help="Repair corrupted MP4 container")
    parser.add_argument("--stego-hide", default=None, help="File to hide inside carrier image")
    parser.add_argument("--stego-extract", action="store_true", help="Extract hidden payload")
    parser.add_argument("--password", default="", help="Password for encryption or decryption")

    args, unknown = parser.parse_known_args()

    input_path = Path(args.input)
    if not input_path.exists():
        console.print(f"[bold red]Error:[/bold red] File not found: {input_path}")
        sys.exit(1)

    # Feature: Steganography Hide
    if args.stego_hide:
        secret_file = Path(args.stego_hide)
        if not secret_file.exists():
            console.print(f"[bold red]Secret file not found:[/bold red] {secret_file}")
            sys.exit(1)
        out_p = Path(args.output) if args.output else input_path.with_name(f"{input_path.stem}_stego.png")
        data = secret_file.read_bytes()
        try:
            hide_payload_in_image(input_path, out_p, data, filename=secret_file.name, password=args.password)
            console.print(f"[bold green]Steganography payload successfully embedded into:[/bold green] {out_p}")
            sys.exit(0)
        except Exception as e:
            console.print(f"[bold red]Steganography failed:[/bold red] {e}")
            sys.exit(1)

    # Feature: Steganography Extract
    if args.stego_extract:
        try:
            res = extract_payload_from_image(input_path, password=args.password)
            out_fn = res["filename"] or f"extracted_from_{input_path.stem}.bin"
            out_p = Path(args.output) if args.output else input_path.parent / out_fn
            out_p.write_bytes(res["data"])
            console.print(f"[bold green]Extracted hidden payload:[/bold green] {out_p} [dim]({len(res['data'])} bytes)[/dim]")
            sys.exit(0)
        except Exception as e:
            console.print(f"[bold red]Steganography extraction failed:[/bold red] {e}")
            sys.exit(1)

    # Resolve output
    target_out = args.output
    if not target_out:
        console.print("[bold red]Please specify target format or output filename.[/bold red]")
        console.print("Example: convert image.jfif png")
        sys.exit(1)

    kwargs = {
        "strip_exif": not args.no_strip_exif,
        "remove_bg": args.remove_bg,
        "auto_redact": args.auto_redact,
        "normalize_lufs": args.normalize_lufs,
        "strip_silence": args.strip_silence,
        "spritesheet": args.spritesheet,
        "repair_container": args.repair,
        "password": args.password,
    }

    if args.vector:
        kwargs["vector_mode"] = "monochrome"

    if args.target_size:
        kwargs["target_size_bytes"] = parse_size_str(args.target_size)

    console.print(f"[dim]Executing conversion:[/dim] [bold white]{input_path.name}[/bold white] -> [bold]{target_out}[/bold]")
    res = convert_file(input_path, target_out, **kwargs)

    if res.success:
        diff_str = f"({res.compression_ratio:.1f}% reduction)" if res.compression_ratio > 0 else ""
        console.print(Panel(
            f"[bold green]CONVERSION COMPLETE[/bold green]\n\n"
            f"[bold white]Output:[/bold white] {res.output_path}\n"
            f"[bold white]Size:[/bold white] {format_bytes(res.original_size)} -> [bold]{format_bytes(res.converted_size)}[/bold] {diff_str}\n"
            f"[dim]{res.message}[/dim]",
            border_style="bright_black"
        ))
    else:
        console.print(Panel(
            f"[bold red]CONVERSION FAILED[/bold red]\n\n{res.message}",
            border_style="bright_black"
        ))
        sys.exit(1)

if __name__ == "__main__":
    main()

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from convert_id.utils.binary_manager import check_dependencies, install_portable_ffmpeg, get_ffmpeg_path

console = Console()

def run_doctor(auto_fix: bool = False):
    """Diagnose all system tools and offer automatic repair."""
    console.print(Panel.fit("[bold white]Convert.id Diagnostic Doctor[/bold white]\n[dim]Checking system engines & external binaries[/dim]", border_style="bright_black"))

    deps = check_dependencies()
    table = Table(border_style="bright_black", header_style="bold white", expand=True)
    table.add_column("Engine / Binary", style="white")
    table.add_column("Status", style="bold")
    table.add_column("Location / Details", style="dim")
    table.add_column("Key Capabilities", style="dim")

    all_ready = True
    missing_ffmpeg = False

    for key, info in deps.items():
        if info["installed"]:
            status = "[bold green]ONLINE[/bold green]"
            path_str = info["path"]
        else:
            status = "[bold red]MISSING[/bold red]"
            path_str = "[dim italic]Not detected in PATH[/dim italic]"
            all_ready = False
            if key == "ffmpeg":
                missing_ffmpeg = True

        caps = ", ".join(info["required_for"][:2]) + "..."
        table.add_row(info["name"], status, path_str, caps)

    console.print(table)

    if missing_ffmpeg:
        console.print("\n[yellow]Notice:[/yellow] FFmpeg is missing. Media conversions (video/audio) will be limited.")
        if auto_fix:
            console.print("[dim]Attempting automatic download of portable FFmpeg...[/dim]")
            def cb(pct, msg):
                console.print(f"[dim]{msg}[/dim]")
            ok = install_portable_ffmpeg(cb)
            if ok:
                console.print("[bold green]Portable FFmpeg installed successfully to ~/.convertid/bin![/bold green]")
            else:
                console.print("[bold red]Automatic installation failed. Please install FFmpeg via winget/brew/apt.[/bold red]")
        else:
            console.print("Run [bold cyan]convert doctor --fix[/bold cyan] to automatically download portable FFmpeg into ~/.convertid/bin.\n")
    elif all_ready:
        console.print("\n[bold green]All core and multimedia engines are operational and ready.[/bold green]\n")

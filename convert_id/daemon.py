import time
import os
import shutil
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from rich.console import Console

from convert_id.engines import convert_file
from convert_id.config import HOTFOLDER_DIR, OUTPUT_DIR

console = Console()

class HotFolderHandler(FileSystemEventHandler):
    def __init__(self, target_ext: str, output_dir: Path, **kwargs):
        self.target_ext = target_ext.lstrip(".")
        self.output_dir = output_dir
        self.kwargs = kwargs
        self.processed = set()

    def on_created(self, event):
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        if file_path in self.processed:
            return

        # Wait briefly for file to finish writing
        time.sleep(1.0)
        
        console.print(f"[dim]Hot-Folder detected:[/dim] [bold white]{file_path.name}[/bold white]")
        try:
            out_file = self.output_dir / f"{file_path.stem}.{self.target_ext}"
            res = convert_file(file_path, str(out_file), **self.kwargs)
            if res.success:
                console.print(f"[bold green]Auto-converted ->[/bold green] {out_file.name} [dim]({res.converted_size} bytes)[/dim]")
                self.processed.add(file_path)
            else:
                console.print(f"[bold red]Failed:[/bold red] {res.message}")
        except Exception as e:
            console.print(f"[bold red]Error processing {file_path.name}:[/bold red] {e}")


def start_watcher(watch_dir: Optional[Path] = None, target_ext: str = "png", output_dir: Optional[Path] = None, **kwargs):
    watch_path = watch_dir or HOTFOLDER_DIR
    out_path = output_dir or OUTPUT_DIR

    watch_path.mkdir(parents=True, exist_ok=True)
    out_path.mkdir(parents=True, exist_ok=True)

    console.print(f"[bold white]Convert.id Auto-Pilot Daemon Active[/bold white]")
    console.print(f"[dim]Watching:[/dim] {watch_path}")
    console.print(f"[dim]Auto-converting to:[/dim] .{target_ext}")
    console.print(f"[dim]Target output folder:[/dim] {out_path}\n[dim]Press Ctrl+C to terminate.[/dim]\n")

    event_handler = HotFolderHandler(target_ext, out_path, **kwargs)
    observer = Observer()
    observer.schedule(event_handler, str(watch_path), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        console.print("\n[dim]Daemon stopped.[/dim]")
    observer.join()

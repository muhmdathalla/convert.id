import cv2
import numpy as np
import pandas as pd
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()

def diff_files(file1: Path, file2: Path, output_diff: Path = None):
    p1 = Path(file1)
    p2 = Path(file2)

    if not p1.exists() or not p2.exists():
        console.print("[bold red]Both files must exist to perform diff.[/bold red]")
        return

    ext1 = p1.suffix.lower()
    ext2 = p2.suffix.lower()

    # Image Pixel Diff
    if ext1 in [".png", ".jpg", ".jpeg", ".webp", ".bmp"] and ext2 in [".png", ".jpg", ".jpeg", ".webp", ".bmp"]:
        img1 = cv2.imread(str(p1))
        img2 = cv2.imread(str(p2))

        if img1.shape != img2.shape:
            # Resize img2 to match img1 for diffing
            img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

        # Calculate absolute difference
        diff = cv2.absdiff(img1, img2)
        gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        changed_pixels = np.count_nonzero(gray_diff > 10)
        total_pixels = img1.shape[0] * img1.shape[1]
        pct = (changed_pixels / total_pixels) * 100.0

        console.print(f"[bold white]Visual Pixel Diff:[/bold white]")
        console.print(f"Dimension: {img1.shape[1]}x{img1.shape[0]}")
        console.print(f"Pixel delta: [bold]{changed_pixels:,}[/bold] / {total_pixels:,} ([bold]{pct:.2f}% modified[/bold])")

        out_path = output_diff or p1.parent / f"diff_{p1.stem}_{p2.stem}.png"
        # Create a heat/highlight mask: grayscale background with red tint on differences
        mask = (gray_diff > 10).astype(np.uint8) * 255
        highlight = img1.copy()
        highlight[mask > 0] = [0, 0, 255] # Red highlight
        cv2.imwrite(str(out_path), highlight)
        console.print(f"[bold green]Saved visual difference highlight to:[/bold green] {out_path}")

    # Tabular / CSV Diff
    elif ext1 in [".csv", ".tsv"] and ext2 in [".csv", ".tsv"]:
        sep1 = "\t" if ext1 == ".tsv" else ","
        sep2 = "\t" if ext2 == ".tsv" else ","
        df1 = pd.read_csv(p1, sep=sep1)
        df2 = pd.read_csv(p2, sep=sep2)

        console.print(f"[bold white]Tabular Data Diff:[/bold white]")
        console.print(f"Rows: File 1 ({len(df1)}) vs File 2 ({len(df2)})")
        console.print(f"Cols: File 1 ({len(df1.columns)}) vs File 2 ({len(df2.columns)})")
        
        # Compare columns
        diff_cols = set(df1.columns) ^ set(df2.columns)
        if diff_cols:
            console.print(f"[yellow]Column Discrepancies:[/yellow] {list(diff_cols)}")
        else:
            console.print("[green]Column schemas match identical.[/green]")

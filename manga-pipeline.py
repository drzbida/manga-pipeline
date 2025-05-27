import argparse
import shutil
import subprocess
import sys
import re
import os
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = Path("./manga_downloads")
EPUB_DIR = Path("./epubs")

DEFAULT_BATCH_SIZE = 20
DEFAULT_CUSTOM_WIDTH = 1264
DEFAULT_CUSTOM_HEIGHT = 1680


def command_exists(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def chapter_sort_key(dir_path: Path) -> int:
    match = re.match(r"c(\d+(?:\.\d+)?)", dir_path.name, re.IGNORECASE)
    if match:
        try:
            return int(float(match.group(1)))
        except ValueError:
            return sys.maxsize
    return sys.maxsize


def run_command(command: list[str], **kwargs) -> subprocess.CompletedProcess:
    print(f"Running: {' '.join(command)}")
    try:
        result = subprocess.run(command, check=True, **kwargs)
        return result
    except FileNotFoundError as e:
        print(f"Error: Command '{command[0]}' not found. {e}", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error: Command failed with exit code {e.returncode}.", file=sys.stderr)
        print(f"Command: {e.cmd}", file=sys.stderr)
        if e.stdout:
            print(f"Stdout: {e.stdout.decode(errors='ignore')}", file=sys.stderr)
        if e.stderr:
            print(f"Stderr: {e.stderr.decode(errors='ignore')}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Download manga chapters, batch them, and convert to EPUB.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    _ = parser.add_argument(
        "-u",
        "--manga-url",
        required=True,
        help="URL of the manga chapter (e.g., https://weebcentral.com/chapters/...). (Required)",
    )

    _ = parser.add_argument(
        "-k",
        "--kcc",
        type=Path,
        required=True,
        help="Path to the KCC (Koreader Comic Converter) executable. (Required)",
    )

    _ = parser.add_argument(
        "--wine",
        action="store_true",
        help="Use Wine to run KCC. (Default: False, set to True if KCC requires Wine)",
    )

    _ = parser.add_argument(
        "-b",
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Number of chapters per EPUB folder. (Default: {DEFAULT_BATCH_SIZE})",
    )
    _ = parser.add_argument(
        "-m",
        "--min-chapter",
        type=str,
        help="Minimum chapter number to download. (Optional)",
    )
    _ = parser.add_argument(
        "-x",
        "--max-chapter",
        type=str,
        help="Maximum chapter number to download. (Optional)",
    )
    _ = parser.add_argument(
        "-w",
        "--custom-width",
        type=int,
        default=DEFAULT_CUSTOM_WIDTH,
        help=f"Custom width for KCC processing. (Default: {DEFAULT_CUSTOM_WIDTH})",
    )
    _ = parser.add_argument(
        "-e",
        "--custom-height",
        type=int,
        default=DEFAULT_CUSTOM_HEIGHT,
        help=f"Custom height for KCC processing. (Default: {DEFAULT_CUSTOM_HEIGHT})",
    )

    args = parser.parse_args()

    if args.batch_size <= 0:
        print("Error: Batch size must be a positive number.", file=sys.stderr)
        sys.exit(1)
    if args.custom_width <= 0:
        print("Error: Custom width must be a positive number.", file=sys.stderr)
        sys.exit(1)
    if args.custom_height <= 0:
        print("Error: Custom height must be a positive number.", file=sys.stderr)
        sys.exit(1)
    if not args.kcc.is_file():
        print(
            f"Error: KCC executable not found at {args.kcc}. Please provide a valid path.",
            file=sys.stderr,
        )
        sys.exit(1)

    # --- Dependency Checks ---
    if not command_exists("gallery-dl"):
        print(
            "Error: gallery-dl command not found. Please install it.", file=sys.stderr
        )
        sys.exit(1)

    if args.wine and not command_exists("wine"):
        print("Error: Wine command not found. Please install it.", file=sys.stderr)
        sys.exit(1)

    print("--- Starting Cleanup ---")
    print(f"Removing previous {DOWNLOAD_DIR} directory (if it exists)...")
    if DOWNLOAD_DIR.exists():
        shutil.rmtree(DOWNLOAD_DIR)

    if EPUB_DIR.exists():
        try:
            confirm = input(
                f"The directory {EPUB_DIR} already exists. Do you want to delete it? (y/n): "
            )
            if confirm.lower() == "y":
                shutil.rmtree(EPUB_DIR)
                print(f"Removed {EPUB_DIR} directory.")
            else:
                print("Exiting without cleanup.")
                sys.exit(0)
        except EOFError:
            print(
                f"Warning: {EPUB_DIR} exists and cannot confirm deletion. Exiting.",
                file=sys.stderr,
            )
            sys.exit(1)
    else:
        print(f"{EPUB_DIR} directory does not exist, no need to remove.")
    print("Cleanup finished.\n")

    print("--- Starting Download ---")
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    gallery_dl_command = ["gallery-dl", "-d", str(DOWNLOAD_DIR)]

    if args.min_chapter and args.max_chapter:
        print(
            f"Attempting to download chapters from {args.min_chapter} to {args.max_chapter}."
        )
        gallery_dl_command.extend(
            ["--chapter-range", f"{args.min_chapter}-{args.max_chapter}"]
        )
    elif args.min_chapter:
        print(f"Attempting to download chapters from {args.min_chapter} onwards.")
        gallery_dl_command.extend(["--chapter-range", f"{args.min_chapter}-"])
    elif args.max_chapter:
        print(f"Attempting to download chapters up to {args.max_chapter}.")
        gallery_dl_command.extend(["--chapter-range", f"-{args.max_chapter}"])

    gallery_dl_command.append(args.manga_url)

    _ = run_command(gallery_dl_command, capture_output=False, text=True)
    print("Download process finished.\n")

    print("--- Starting Rearrangement ---")
    manga_base_dir = DOWNLOAD_DIR / "weebcentral"
    if not manga_base_dir.is_dir():
        print(
            f"Error: Expected download directory {manga_base_dir} not found.",
            file=sys.stderr,
        )
        sys.exit(1)

    manga_name_dirs = [d for d in manga_base_dir.iterdir() if d.is_dir()]
    if not manga_name_dirs:
        print(
            f"Error: Could not find the manga directory in {manga_base_dir}. No chapters downloaded or unexpected structure.",
            file=sys.stderr,
        )
        sys.exit(1)

    manga_name_dir = manga_name_dirs[0]
    manga_name = manga_name_dir.name
    print(f"Found manga: {manga_name} in {manga_name_dir}")

    chapter_dirs = sorted(
        [
            d
            for d in manga_name_dir.iterdir()
            if d.is_dir() and d.name.lower().startswith("c")
        ],
        key=chapter_sort_key,
    )

    total_chapters = len(chapter_dirs)
    if total_chapters == 0:
        print(
            f"No chapter folders found starting with 'c' in {manga_name_dir}. No chapters to rearrange."
        )
        sys.exit(0)

    print(f"Found {total_chapters} chapter folders.")

    current_chapter_index = 0
    processed_batch_folders = []

    while current_chapter_index < total_chapters:
        start_index = current_chapter_index
        end_index = min(current_chapter_index + args.batch_size - 1, total_chapters - 1)

        start_num = re.search(
            r"c(\d+(?:\.\d+)?)", chapter_dirs[start_index].name, re.I
        ).group(1)
        end_num = re.search(
            r"c(\d+(?:\.\d+)?)", chapter_dirs[end_index].name, re.I
        ).group(1)

        batch_folder_name = manga_name_dir / f"{manga_name}_{start_num}_{end_num}"
        batch_folder_name.mkdir(parents=True, exist_ok=True)
        processed_batch_folders.append(batch_folder_name)

        print(f"Creating batch folder: {batch_folder_name.name}")

        for i in range(start_index, end_index + 1):
            src = chapter_dirs[i]
            dst = batch_folder_name / src.name
            print(f"  Moving {src.name} to {batch_folder_name.name}/")
            shutil.move(str(src), str(dst))

        current_chapter_index = end_index + 1

    print("Rearranging finished.\n")

    print("--- Starting KCC Processing ---")
    EPUB_DIR.mkdir(parents=True, exist_ok=True)
    abs_epub_dir = EPUB_DIR.resolve()

    if not processed_batch_folders:
        print("No batch folders were created or found to process.")
        sys.exit(0)

    print(f"Found {len(processed_batch_folders)} batch folders to process.")
    print(f"EPUB files will be saved to: {abs_epub_dir}")

    for folder in processed_batch_folders:
        if folder.is_dir():
            print(f"Processing folder: {folder.name}")
            abs_folder_path = folder.resolve()

            env = os.environ.copy()
            convert_cmd = [
                str(args.kcc),
                "--manga-style",
                "--profile=OTHER",
                "--splitter=2",
                "--cropping=2",
                f"--customwidth={args.custom_width}",
                f"--customheight={args.custom_height}",
                "--format=EPUB",
                "--stretch",
                "-o",
                str(abs_epub_dir),
                str(abs_folder_path),
            ]

            if args.wine:
                convert_cmd = ["wine"] + convert_cmd
                env["WINEDEBUG"] = "-all"

            try:
                _ = subprocess.run(
                    convert_cmd,
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    env=env,
                )
                print(f"Finished processing {folder.name}.")
            except subprocess.CalledProcessError as e:
                print(
                    f"Warning: KCC processing might have failed for {folder.name}.",
                    file=sys.stderr,
                )
                if e.stderr:
                    print(
                        f"  KCC Stderr: {e.stderr.decode(errors='ignore').strip()}",
                        file=sys.stderr,
                    )

    print("KCC processing finished.\n")

    print("--- Starting Final Cleanup ---")
    print(f"Removing {DOWNLOAD_DIR} directory...")
    shutil.rmtree(DOWNLOAD_DIR)
    print("Cleanup finished.\n")

    print(f"Script finished successfully. EPUBs are in {EPUB_DIR}")


if __name__ == "__main__":
    main()

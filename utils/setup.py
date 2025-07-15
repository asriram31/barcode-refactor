import csv
import os
from typing import List, Tuple


def remove_extension(path: str) -> str:
    return os.path.splitext(path)[0]


def create_output_directories(filepath: str) -> Tuple[str, str]:
    """Create output directories for analysis results."""
    figure_dir_name = remove_extension(filepath) + " BARCODE Output"
    if not os.path.exists(figure_dir_name):
        os.makedirs(figure_dir_name)
    return figure_dir_name


def create_channel_output_dir(figure_dir_name: str, channel: int) -> str:
    """Create channel-specific output directory."""
    fig_channel_dir_name = os.path.join(figure_dir_name, f"Channel {channel}")
    if not os.path.exists(fig_channel_dir_name):
        os.makedirs(fig_channel_dir_name)
    return fig_channel_dir_name


def discover_files(root_dir: str) -> List[str]:
    """Walk through directory and return list of valid file paths."""
    # Single file mode
    if os.path.isfile(root_dir):
        return [root_dir]

    # Directory mode - walk and find valid files
    valid_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Keep all directories (original behavior)
        dirnames[:] = [d for d in dirnames]

        for filename in filenames:
            # Skip hidden files
            if filename.startswith("._"):
                continue

            # Only process .tif and .nd2 files
            if filename.endswith(".tif") or filename.endswith(".nd2"):
                file_path = os.path.join(dirpath, filename)
                valid_files.append(file_path)

    return valid_files


def setup_paths(root_dir: str, is_single_file: bool):
    """Setup filepaths for data and output files."""

    base_path = root_dir if not is_single_file else os.path.dirname(root_dir)
    base_name = remove_extension(os.path.basename(root_dir))

    ff_name = (
        "failed_files.txt" if not is_single_file else f"{base_name}_failed_files.txt"
    )
    time_name = "time.txt" if not is_single_file else f"{base_name}_time.txt"

    ff_filepath = os.path.join(base_path, ff_name)
    time_filepath = os.path.join(base_path, time_name)

    open(ff_filepath, "w").close()

    return base_path, base_name, ff_filepath, time_filepath


def setup_csv_writer(filename: str):
    """Setup CSV writer and file handle."""
    myfile = open(filename, "w")
    csvwriter = csv.writer(myfile)
    return csvwriter, myfile

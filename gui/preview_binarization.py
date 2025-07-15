import tkinter as tk
from tkinter import filedialog

import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import numpy as np

from utils.analysis import binarize

try:
    import tifffile
except ImportError:
    tifffile = None
try:
    from nd2reader import ND2Reader
except ImportError:
    ND2Reader = None


def load_first_frame(file_path):
    ext = file_path.lower().split(".")[-1]
    if ext in ["tif", "tiff"] and tifffile:
        img = tifffile.imread(file_path)
        if img.ndim == 3:
            return img[0]
        if img.ndim == 4:
            return img[0, :, :, 0]
        return img
    elif ext == "nd2" and ND2Reader:
        with ND2Reader(file_path) as images:
            # ND2Reader returns an iterable over frames; grab the first frame
            # It may return a (y, x) or (c, y, x) array; handle both
            arr = np.array(images[0])
            # If ND2 contains channels, select channel 0 by default
            if arr.ndim == 3:
                arr = arr[0]
            return arr
    raise ValueError(
        "Only TIFF and ND2 are supported in this demo, and required libraries must be installed."
    )


def main():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select TIFF or ND2 file",
        filetypes=(
            ("Image files", "*.tif *.tiff *.nd2"),
            ("TIFF files", "*.tif *.tiff"),
            ("ND2 files", "*.nd2"),
        ),
    )
    if not file_path:
        print("No file selected.")
        return
    image = load_first_frame(file_path)
    initial_offset = 0.1

    fig, ax = plt.subplots()
    plt.subplots_adjust(bottom=0.25)
    bin_img = binarize(image, initial_offset)
    im = ax.imshow(bin_img, cmap="gray", vmin=0, vmax=1)
    ax.set_title(f"Offset: {initial_offset:.2f}")
    ax.axis("off")
    ax_offset = plt.axes([0.25, 0.1, 0.65, 0.03], facecolor="lightgoldenrodyellow")
    s_offset = Slider(
        ax_offset, "Offset", -1.0, 1.0, valinit=initial_offset, valstep=0.05
    )

    def update(val):
        offset = s_offset.val
        bin_img = binarize(image, offset)
        im.set_data(bin_img)
        ax.set_title(f"Offset: {offset:.2f}")
        fig.canvas.draw_idle()

    s_offset.on_changed(update)
    plt.show()


if __name__ == "__main__":
    main()

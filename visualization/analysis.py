import os
from typing import List

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.axes import Axes

from analysis.flow import FlowOutput


def save_binarization_plot(
    void_percent_gain_list: np.ndarray,
    island_percent_gain_list: np.ndarray,
    num_frames: int,
    frame_step: int,
    start_index: int,
    stop_index: int,
) -> plt.Figure:
    """Create binarization analysis plot."""

    fig, ax = plt.subplots(figsize=(5, 5))

    plot_range = np.arange(
        start_index * frame_step, stop_index * frame_step, frame_step
    )
    plot_range[-1] = (
        num_frames - 1
        if stop_index * frame_step >= num_frames
        else stop_index * frame_step
    )

    ax.plot(
        plot_range,
        100 * void_percent_gain_list[start_index:stop_index],
        c="b",
        label="Original Void Size Proportion",
    )
    ax.plot(
        plot_range,
        100 * island_percent_gain_list[start_index:stop_index],
        c="r",
        label="Original Island Size Proportion",
    )
    ax.set_xticks(plot_range[::10])
    if stop_index * frame_step >= num_frames != 0:
        ax.set_xlim(left=None, right=num_frames - 1)
    ax.set_xlabel("Frames")
    ax.set_ylabel("Percentage of Original Size")
    ax.legend()

    return fig


def save_binarization_visualization(
    original_frame: np.ndarray, binarized_frame: np.ndarray, frame_idx: int, name: str
):
    """Save side-by-side comparison of original and binarized frames."""

    fig, axs = plt.subplots(ncols=2, figsize=(10, 5))
    axs[0].imshow(original_frame, cmap="gray")
    axs[1].imshow(binarized_frame, cmap="gray")

    # Format ticks to show actual pixel coordinates (accounting for downsampling)
    ticks_adj = ticker.FuncFormatter(lambda x, pos: f"{x * 2:g}")
    axs[1].xaxis.set_major_formatter(ticks_adj)
    axs[1].yaxis.set_major_formatter(ticks_adj)

    axs[0].axis("off")
    axs[1].axis("off")

    figpath = os.path.join(name, f"Binarization Frame {frame_idx} Comparison.png")
    plt.savefig(figpath)
    plt.close("all")


def save_flow_visualization(
    flow: FlowOutput, start_frame: int, name: str, downsample: int
):
    """Save flow field visualization as PNG."""

    downU, downV, directions, speed = flow

    img_shape = downU.shape[0] / downU.shape[1]
    fig, ax = plt.subplots(figsize=(10 * img_shape, 10))
    assert isinstance(ax, Axes)

    ax.quiver(downU, downV, color="blue")

    ticks_adj = ticker.FuncFormatter(lambda x, pos: f"{x * downsample:g}")
    ax.xaxis.set_major_formatter(ticks_adj)
    ax.yaxis.set_major_formatter(ticks_adj)
    ax.set_aspect(aspect=1, adjustable="box")

    figpath = os.path.join(name, f"Frame {start_frame} Flow Field.png")
    fig.savefig(figpath)
    plt.close("all")


def save_intensity_plot(
    first_frame: np.ndarray,
    last_frame: np.ndarray,
    first_frame_idx: int,
    last_frame_idx: int,
    max_intensity: float,
) -> plt.Figure:
    """Create intensity distribution comparison plot."""

    fig, ax = plt.subplots(figsize=(5, 5))

    bins_width = 3
    set_bins = np.arange(0, max_intensity, bins_width)

    # Calculate histograms
    i_count, bins = np.histogram(first_frame.flatten(), bins=set_bins, density=True)
    f_count, bins = np.histogram(last_frame.flatten(), bins=set_bins, density=True)
    center_bins = (bins[1] - bins[0]) / 2
    plt_bins = bins[0:-1] + center_bins

    # Calculate means for vertical lines
    i_mean = np.mean(first_frame)
    f_mean = np.mean(last_frame)

    # Plot distributions
    ax.plot(
        plt_bins[::10],
        i_count[::10],
        "^-",
        ms=4,
        c="darkred",
        alpha=0.6,
        label=f"Frame {first_frame_idx} Intensity Distribution",
    )
    ax.plot(
        plt_bins[::10],
        f_count[::10],
        "v-",
        ms=4,
        c="purple",
        alpha=0.6,
        label=f"Frame {last_frame_idx} Intensity Distribution",
    )

    # Add mean lines
    ax.axvline(
        x=i_mean,
        ms=4,
        c="darkred",
        alpha=1,
        label=f"Frame {first_frame_idx} Mean",
    )
    ax.axvline(
        x=f_mean, ms=4, c="purple", alpha=1, label=f"Frame {last_frame_idx} Mean"
    )

    ax.axhline(0, color="dimgray", alpha=0.6)
    ax.set_xlabel("Pixel intensity value")
    ax.set_ylabel("Probability")
    ax.set_yscale("log")
    ax.set_xlim(0, max_intensity)
    ax.legend()

    return fig


def create_summary_visualization(figures: List[plt.Figure], output_path: str) -> None:
    """Create combined summary plot from analysis figures."""
    if not figures:
        return

    num_figs = len(figures)
    fig = plt.figure(figsize=(5 * num_figs, 5))

    for i, source_fig in enumerate(figures):
        ax = source_fig.axes[0]
        ax.figure = fig
        fig.add_axes(ax)
        if num_figs == 2:
            # Position axes side by side
            if i == 0:
                ax.set_position([1.5 / 10, 1 / 10, 4 / 5, 4 / 5])
            else:
                ax.set_position([11.5 / 10, 1 / 10, 4 / 5, 4 / 5])

    plt.savefig(output_path)
    plt.close(fig)
    plt.close("all")

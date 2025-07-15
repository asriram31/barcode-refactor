import os
from typing import Tuple, List, Optional

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import kurtosis

from core import IntensityDistributionConfig, OutputConfig, IntensityResults
from utils import vprint
from utils.analysis import (
    top_ten_average,
    calc_mode_skewness,
    calc_median_skewness,
    calc_mode,
)
from utils.setup import setup_csv_writer


def calculate_frame_indices(
    num_frames: int,
    int_config: IntensityDistributionConfig,
) -> Tuple[int, int, int]:
    """Calculate frame indices for intensity analysis."""

    first_frame_idx = int_config.first_frame.get()
    last_frame_idx = int_config.last_frame.get()
    frames_percent = int_config.frames_evaluation_percent.get()

    num_frames_analysis = int(np.ceil(frames_percent * num_frames))

    # Handle last frame auto-detection
    if last_frame_idx == 0:
        last_frame_idx = num_frames

    # Validate and adjust frame ranges (matching original logic exactly, including bug)
    if first_frame_idx + num_frames_analysis >= num_frames:
        first_frame_idx = 0
    if last_frame_idx + num_frames - num_frames_analysis < 0:  # Original has bug here
        last_frame_idx = 0

    return first_frame_idx, last_frame_idx, num_frames_analysis


def calculate_frame_metrics(
    frames_data: List[np.ndarray],
) -> Tuple[List[float], List[float], List[float]]:
    """Calculate kurtosis, median skew, and mode skew for a set of frames."""

    def calc_frame_metric(metric, data: List[np.ndarray]) -> List[float]:
        """Calculate a metric for each frame in the data."""
        mets = []
        for i in range(len(data)):
            met = metric(data[i].flatten())
            mets.append(met)
        return mets

    kurtosis_values = calc_frame_metric(kurtosis, frames_data)
    median_skew_values = calc_frame_metric(calc_median_skewness, frames_data)
    mode_skew_values = calc_frame_metric(calc_mode_skewness, frames_data)

    return kurtosis_values, median_skew_values, mode_skew_values


def write_intensity_data(
    csvwriter, frames_data: List[np.ndarray], frame_indices: List[int]
):
    """Write intensity histogram data to CSV."""
    if not csvwriter:
        return

    for frame_data, frame_idx in zip(frames_data, frame_indices):
        csvwriter.writerow([f"Frame {frame_idx}"])
        frame_values, frame_counts = np.unique(frame_data, return_counts=True)
        csvwriter.writerow(frame_values)
        csvwriter.writerow(frame_counts)
        csvwriter.writerow([])


def analyze_intensity_metrics(
    first_frames_data: List[np.ndarray], last_frames_data: List[np.ndarray]
) -> Tuple[float, float, float, float, float, float]:
    """Calculate intensity distribution metrics from frame data."""
    # Calculate metrics for first and last frame sets
    first_kurt, first_median_skew, first_mode_skew = calculate_frame_metrics(
        first_frames_data
    )
    last_kurt, last_median_skew, last_mode_skew = calculate_frame_metrics(
        last_frames_data
    )

    # Combine and calculate aggregated metrics
    total_kurt = first_kurt + last_kurt
    total_median_skew = first_median_skew + last_median_skew
    total_mode_skew = first_mode_skew + last_mode_skew

    max_kurtosis = top_ten_average(total_kurt)
    max_median_skew = top_ten_average(total_median_skew)
    max_mode_skew = top_ten_average(total_mode_skew)

    # Calculate differences between first and last frames
    kurtosis_diff = np.mean(np.array(last_kurt)) - np.mean(np.array(first_kurt))
    median_skew_diff = np.mean(np.array(last_median_skew)) - np.mean(
        np.array(first_median_skew)
    )
    mode_skew_diff = np.mean(np.array(last_mode_skew)) - np.mean(
        np.array(first_mode_skew)
    )

    return (
        max_kurtosis,
        max_median_skew,
        max_mode_skew,
        kurtosis_diff,
        median_skew_diff,
        mode_skew_diff,
    )


def analyze_intensity_distribution(
    file: np.ndarray,
    name: str,
    channel: int,
    int_config: IntensityDistributionConfig,
    out_config: OutputConfig,
) -> Tuple[Optional[plt.Figure], IntensityResults]:
    """
    Analyze intensity distribution changes between first and last frames.

    Returns:
        Tuple of (matplotlib figure or None, IntensityResults)
    """
    vprint("Beginning Intensity Distribution Analysis...")

    image = file[:, :, :, channel]
    num_frames = image.shape[0]

    # Error Checking: Empty Image
    if (image == 0).all():
        return None, IntensityResults(flag=1)

    # Calculate frame indices using extracted function
    first_frame_idx, last_frame_idx, num_frames_analysis = calculate_frame_indices(
        num_frames, int_config
    )

    # Extract frame data
    first_frames_data = [
        image[i]
        for i in range(first_frame_idx, first_frame_idx + num_frames_analysis, 1)
    ]
    last_frames_data = [
        image[i] for i in range(last_frame_idx - num_frames_analysis, last_frame_idx, 1)
    ]

    # Check for saturation (flag = 2)
    flag = 0
    if all(
        [
            np.max(frame) == calc_mode(frame)
            for frame in first_frames_data + last_frames_data
        ]
    ):
        flag = 2

    # Setup CSV writer if needed
    csvwriter, myfile = None, None
    if out_config.save_intermediates.get():
        filename = os.path.join(name, "IntensityDistribution.csv")
        csvwriter, myfile = setup_csv_writer(filename)

        # Write data for both first and last frame sets
        first_indices = list(
            range(first_frame_idx, first_frame_idx + num_frames_analysis)
        )
        last_indices = list(range(last_frame_idx - num_frames_analysis, last_frame_idx))

        write_intensity_data(csvwriter, first_frames_data, first_indices)
        write_intensity_data(csvwriter, last_frames_data, last_indices)

    # Calculate intensity metrics using extracted function
    (
        max_kurtosis,
        max_median_skew,
        max_mode_skew,
        kurtosis_diff,
        median_skew_diff,
        mode_skew_diff,
    ) = analyze_intensity_metrics(first_frames_data, last_frames_data)

    # Create visualization plot
    fig = None
    if out_config.save_graphs.get():
        first_frame = image[first_frame_idx]
        # Handle last frame selection (matching original logic)
        final_frame_idx = (
            last_frame_idx - 1 if last_frame_idx <= num_frames else num_frames - 1
        )
        last_frame = image[final_frame_idx]
        max_intensity = 1.1 * np.max(image)

        from visualization import save_intensity_plot

        fig = save_intensity_plot(
            first_frame, last_frame, first_frame_idx, final_frame_idx, max_intensity
        )

    # Clean up CSV file
    if myfile:
        myfile.close()

    results = IntensityResults(
        max_kurtosis=max_kurtosis,
        max_median_skew=max_median_skew,
        max_mode_skew=max_mode_skew,
        kurtosis_diff=kurtosis_diff,
        median_skew_diff=median_skew_diff,
        mode_skew_diff=mode_skew_diff,
        flag=flag,
    )

    return fig, results

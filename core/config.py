from abc import ABC
from dataclasses import dataclass, field, Field, MISSING
from typing import Dict, Any, List

import tkinter as tk
from tkinter import Variable
import yaml


def tk_int(value: int = 0) -> tk.IntVar:
    return field(default_factory=lambda: tk.IntVar(value=value))


def tk_double(value: float = 0.0) -> tk.DoubleVar:
    return field(default_factory=lambda: tk.DoubleVar(value=value))


def tk_bool(value: bool = False) -> tk.BooleanVar:
    return field(default_factory=lambda: tk.BooleanVar(value=value))


def tk_string(value: str = "") -> tk.StringVar:
    return field(default_factory=lambda: tk.StringVar(value=value))


@dataclass
class BaseConfig(ABC):
    """Base class for config sections with automatic tkinter variable creation."""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseConfig":
        """Create a config instance from a dictionary, auto-creating tkinter variables."""
        kwargs = {}

        # Iterate over all fields in the dataclass
        for field_name, field_info in cls.__dataclass_fields__.items():

            assert isinstance(
                field_info, Field
            ), f"Expected {field_name} to be a dataclass field"

            # Get the default factory to determine variable type
            default_factory = field_info.default_factory

            if field_name not in data:
                raise ValueError(
                    f"Missing required field '{field_name}' in configuration data"
                )

            value = data[field_name]

            if not default_factory or default_factory == MISSING:
                # If no default factory, use the value directly
                kwargs[field_name] = value
                print(
                    f"No default factory for {field_name} of type {type(value)}, using value directly"
                )
                continue

            # If a default factory is defined, create the tkinter variable
            tk_var = default_factory()
            assert isinstance(
                tk_var, Variable
            ), f"Expected {field_name} to be a tkinter Variable instance"

            tk_var.set(value)
            kwargs[field_name] = tk_var

        return cls(**kwargs)


@dataclass
class InputConfig(BaseConfig):
    """File and data input configuration."""

    file_path: tk.StringVar = tk_string()
    dir_path: tk.StringVar = tk_string()
    mode: tk.StringVar = tk_string("file")  # "file", "dir", "agg"
    configuration_file: tk.StringVar = tk_string()


@dataclass
class ChannelConfig(BaseConfig):
    """Channel selection and processing configuration."""

    parse_all_channels: tk.BooleanVar = tk_bool()
    selected_channel: tk.IntVar = tk_int(0)  # -3 to 4 range


@dataclass
class QualityConfig(BaseConfig):
    """Data quality and acceptance criteria."""

    accept_dim_images: tk.BooleanVar = tk_bool()
    accept_dim_channels: tk.BooleanVar = tk_bool()


@dataclass
class AnalysisConfig(BaseConfig):
    """Analysis module selection and coordination."""

    enable_binarization: tk.BooleanVar = tk_bool()
    enable_optical_flow: tk.BooleanVar = tk_bool()
    enable_intensity_distribution: tk.BooleanVar = tk_bool()


@dataclass
class OutputConfig(BaseConfig):
    """Output generation and format configuration."""

    verbose: tk.BooleanVar = tk_bool()
    save_graphs: tk.BooleanVar = tk_bool()
    save_intermediates: tk.BooleanVar = tk_bool()
    generate_dataset_barcode: tk.BooleanVar = tk_bool()


@dataclass
class BinarizationConfig(BaseConfig):
    """Binarization analysis parameters."""

    threshold_offset: tk.DoubleVar = tk_double(0.1)  # -1.0 to 1.0
    frame_step: tk.IntVar = tk_int(10)  # 1 to 100
    frame_start_percent: tk.DoubleVar = tk_double(0.9)  # 0.5 to 0.9
    frame_stop_percent: tk.DoubleVar = tk_double(1.0)  # 0.9 to 1.0


@dataclass
class OpticalFlowConfig(BaseConfig):
    """Optical flow analysis parameters."""

    frame_step: tk.IntVar = tk_int(10)
    window_size: tk.IntVar = tk_int(32)
    downsample_factor: tk.IntVar = tk_int(8)  # 1 to 1000
    nm_pixel_ratio: tk.DoubleVar = tk_double(1.0)  # 1 to 1,000,000
    frame_interval_s: tk.IntVar = tk_int(
        1
    )  # 1 to 1000 - matches main.py frame_interval_var


@dataclass
class IntensityDistributionConfig(BaseConfig):
    """Intensity distribution analysis parameters."""

    first_frame: tk.IntVar = tk_int(1)  # minimum 1
    last_frame: tk.IntVar = tk_int(0)  # 0 means auto-detect last frame
    frames_evaluation_percent: tk.DoubleVar = tk_double(0.1)  # 0.01 to 0.2


@dataclass
class PreviewConfig(BaseConfig):
    """GUI preview and visualization settings."""

    sample_file: tk.StringVar = tk_string()
    enable_live_preview: tk.BooleanVar = tk_bool(True)


@dataclass
class AggregationConfig(BaseConfig):
    """CSV aggregation and post-processing configuration."""

    output_location: tk.StringVar = tk_string()
    generate_barcode: tk.BooleanVar = tk_bool()
    sort_parameter: tk.StringVar = tk_string("Default")  # One of the metric headers
    normalize_barcode: tk.BooleanVar = tk_bool()
    csv_paths_list: List[str] = field(default_factory=list)  # List of CSV file paths


@dataclass
class BarcodeConfig:
    """Main configuration container for BARCODE application."""

    channels: ChannelConfig = field(default_factory=ChannelConfig)
    quality: QualityConfig = field(default_factory=QualityConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    output: OutputConfig = field(default_factory=OutputConfig)

    # Analysis-specific configurations
    binarization: BinarizationConfig = field(default_factory=BinarizationConfig)
    optical_flow: OpticalFlowConfig = field(default_factory=OpticalFlowConfig)
    intensity_distribution: IntensityDistributionConfig = field(
        default_factory=IntensityDistributionConfig
    )

    def save_to_yaml(self, filepath: str) -> None:
        """Save configuration to YAML file."""
        # Extract values from Tkinter variables for serialization

        config_data = {}
        for subconfig_class_name, _ in self.__dataclass_fields__.items():

            # Get the config object
            subconfig_obj = getattr(self, subconfig_class_name)
            assert isinstance(
                subconfig_obj, BaseConfig
            ), f"Expected {subconfig_class_name} to be a BaseConfig instance"

            subconfig_data = {}

            for attr_name, _ in subconfig_obj.__dataclass_fields__.items():

                # Extract the tkinter variable
                tk_var = getattr(subconfig_obj, attr_name)
                assert isinstance(
                    tk_var, Variable
                ), f"Expected {attr_name} to be a tkinter Variable instance"

                subconfig_data[attr_name] = tk_var.get()

            # Add the data from this config object
            config_data[subconfig_class_name] = subconfig_data

        with open(filepath, "w") as f:
            yaml.dump(config_data, f, default_flow_style=False, indent=2)

    @classmethod
    def load_from_yaml(cls, filepath: str) -> "BarcodeConfig":
        """Load configuration from YAML file."""
        with open(filepath, "r") as f:
            config_data = yaml.safe_load(f)

        if not isinstance(config_data, dict):
            raise ValueError("Error loading YAML: expected a dictionary structure")

        kwargs = {}
        for subconfig_class_name, subconfig_data in config_data.items():

            print(f"Processing subconfig: {subconfig_class_name}")
            print(f"Subconfig data: {subconfig_data}")
            assert (
                subconfig_class_name in cls.__dataclass_fields__
            ), f"Unknown configuration section: {subconfig_class_name}"

            field_info = cls.__dataclass_fields__[subconfig_class_name]
            subconfig_class = field_info.default_factory

            assert callable(
                subconfig_class
            ), f"Expected {subconfig_class_name} to be a callable class, got {subconfig_class}"
            assert issubclass(
                subconfig_class, BaseConfig
            ), f"Expected {subconfig_class_name} to be a subclass of BaseConfig"

            # Get the config class and create new instance from dict
            kwargs[subconfig_class_name] = subconfig_class.from_dict(subconfig_data)

        return cls(**kwargs)

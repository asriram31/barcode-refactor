import threading
import traceback

import matplotlib
from tkinter import ttk, messagebox

from core import BarcodeConfig, InputConfig, PreviewConfig, AggregationConfig, ChannelConfig
from gui import (
    create_barcode_frame,
    create_binarization_frame,
    create_execution_frame,
    create_flow_frame,
    create_intensity_frame,
    setup_log_window,
    setup_main_window,
    setup_scrollable_container,
)

matplotlib.use("Agg")


def create_tabs(
    parent,
    config: BarcodeConfig,
    input_config: InputConfig,
    preview_config: PreviewConfig,
    aggregation_config: AggregationConfig,
):
    """Create all tabs using our extracted components"""
    notebook = ttk.Notebook(parent, takefocus=0)
    notebook.pack(fill="both", expand=True)

    # Create all tabs
    execution_frame = create_execution_frame(notebook, config, input_config)
    binarization_frame = create_binarization_frame(
        notebook, config, preview_config, input_config
    )
    flow_frame = create_flow_frame(notebook, config)
    intensity_frame = create_intensity_frame(notebook, config)
    barcode_frame = create_barcode_frame(notebook, config, aggregation_config)

    # Add tabs to notebook
    notebook.add(execution_frame, text="Execution Settings")
    notebook.add(binarization_frame, text="Binarization Settings")
    notebook.add(flow_frame, text="Optical Flow Settings")
    notebook.add(intensity_frame, text="Intensity Distribution Settings")
    notebook.add(barcode_frame, text="Barcode Generator + CSV Aggregator")

    return notebook


def create_processing_worker(
    config: BarcodeConfig,
    input_config: InputConfig,
    aggregation_config: AggregationConfig,
):
    """Create the worker function for processing in background thread"""

    if input_config.configuration_file.get():
        try:
            config = BarcodeConfig.load_from_yaml(input_config.configuration_file.get())
        except Exception as e:
            messagebox.showerror("Error reading config file", str(e))
            return

    def worker():
        try:
            mode = input_config.mode.get()

            if mode == "agg":
                from utils.writer import generate_aggregate_csv

                # Handle CSV aggregation
                combined_location = aggregation_config.output_location.get()
                generate_agg_barcode = aggregation_config.generate_barcode.get()
                sort_param = aggregation_config.sort_parameter.get()
                csv_paths = aggregation_config.csv_paths_list

                if not csv_paths:
                    messagebox.showerror(
                        "Error", "No CSV files selected for aggregation."
                    )
                    return
                if not combined_location:
                    messagebox.showerror("Error", "No aggregate location specified.")
                    return

                sort_choice = None if sort_param == "Default" else sort_param
                generate_aggregate_csv(
                    csv_paths, combined_location, generate_agg_barcode, sort_choice
                )

            else:
                from core.pipeline import run_analysis

                # Handle file/directory processing
                file_path = input_config.file_path.get()
                dir_path = input_config.dir_path.get()

                if not (dir_path or file_path):
                    messagebox.showerror(
                        "Error", "No file or directory has been selected."
                    )
                    return

                channels = config.channels.parse_all_channels.get()
                channel_selection = config.channels.selected_channel.get()
                if not (channels or (channel_selection is not None)):
                    messagebox.showerror("Error", "No channel has been specified.")
                    return

                dir_name = dir_path if dir_path else file_path

                run_analysis(dir_name, config)

        except Exception as e:
            print(f"Error during processing: {e}")
            print(traceback.format_exc())
            messagebox.showerror("Error during processing", str(e))

        finally:
            messagebox.showinfo(
                "Processing Complete", "Analysis has finished successfully."
            )

    return worker


def main():
    """Main application entry point"""

    # Setup main window
    root = setup_main_window()
    scrollable_frame, canvas = setup_scrollable_container(root)

    # Create configurations
    config = BarcodeConfig()
    input_config = InputConfig()
    preview_config = PreviewConfig()
    aggregation_config = AggregationConfig()
    channel_config = ChannelConfig()

    # Create tabs
    create_tabs(
        scrollable_frame, config, input_config, preview_config, aggregation_config
    )

    # Run button
    def on_run():
        setup_log_window(root)
        worker = create_processing_worker(config, input_config, aggregation_config)
        threading.Thread(target=worker, daemon=True).start()

    run_button = ttk.Button(root, text="Run", command=on_run)
    run_button.grid(row=1, column=0, pady=10, sticky="n")

    # Configure canvas sizing
    root.update_idletasks()
    bbox = canvas.bbox("all")
    if bbox:
        content_width = bbox[2] - bbox[0]
        content_height = bbox[3] - bbox[1]
        canvas.config(width=content_width, height=content_height)
        root.update_idletasks()

    root.mainloop()


if __name__ == "__main__":
    main()

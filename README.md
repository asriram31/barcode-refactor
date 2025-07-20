# BARCODE Refactor

A comprehensive architectural refactor of the [BARCODE](https://github.com/softmatterdb/barcode) repository.  
Essentially no changes to core functionality or GUI — just a cleaner, more modular structure.

## Highlights

- **Modular Architecture**: Separated core logic, GUI, analysis, visualization, and utilities into focused modules
- **Type-Safe Config & Results**: Dataclass-based configs and structured analysis outputs
- **Headless Procesing**: Core analysis pipeline no longer requires GUI dependencies
- **Auto-Generated GUI Config**: Maintains type safety while eliminating code duplication

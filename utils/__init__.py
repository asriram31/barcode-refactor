from utils.timing import Timer

# Global verbose setting
_VERBOSE = False


def set_verbose(verbose: bool):
    """Set global verbose mode."""
    global _VERBOSE
    _VERBOSE = verbose


def vprint(*args, **kwargs):
    """Global verbose print function."""
    if _VERBOSE:
        print(*args, **kwargs, flush=True)


__all__ = [
    "Timer",
    "vprint",
    "set_verbose",
]

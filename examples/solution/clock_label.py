def format_elapsed(seconds):
    """Format nonnegative whole seconds as MM:SS, retaining total minutes."""
    minutes, remaining = divmod(seconds, 60)
    return f"{minutes:02d}:{remaining:02d}"

from datetime import datetime


def log(*args, **kwargs):
    """Print with YYYY-MM-DD HH:MM:SS timestamp prefix."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}]", *args, **kwargs, flush=True)

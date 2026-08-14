import difflib


def generate_diff(original: str, revised: str) -> str:
    """Return a simple unified diff between original and revised text."""
    orig_lines = original.splitlines(keepends=True)
    rev_lines = revised.splitlines(keepends=True)
    return "".join(difflib.unified_diff(orig_lines, rev_lines, fromfile='original', tofile='revised'))

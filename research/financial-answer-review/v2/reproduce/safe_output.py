"""Fresh local output directories for the two portable reproduction helpers."""
from pathlib import Path


def fresh_output(path, input_root=None):
    path = Path(path).absolute()
    if path.exists() or path.is_symlink() or any(p.is_symlink() for p in path.parents):
        raise ValueError('Output must be fresh and not symlinked')
    path = path.resolve()
    if input_root is not None and path.is_relative_to(Path(input_root).resolve()):
        raise ValueError('Output must be outside the input archive')
    path.mkdir(parents=True, exist_ok=False)
    return path

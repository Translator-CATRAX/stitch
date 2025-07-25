import argparse
import itertools
import urllib
from typing import Any, Iterator, TypeVar, Union, cast

import bmt
import numpy as np
import requests


def get_biolink_categories(log_work: bool = False) -> set[str]:
    tk = bmt.Toolkit()
    if log_work:
        ver = tk.get_model_version()
        print(f"loading Biolink model version: {ver}")
    return set(tk.get_all_classes(formatted=True))


def namespace_to_dict(namespace: argparse.Namespace) -> dict[str, Any]:
    return {
        k: namespace_to_dict(v) if isinstance(v, argparse.Namespace) else v
        for k, v in vars(namespace).items()
    }


T = TypeVar("T", bound=object)
def nan_to_none(o: Union[float, T]) -> Union[None, T]:
    if isinstance(o, float) and np.isnan(o):
        return None
    return cast(T, o)

SECS_PER_MIN = 60
SECS_PER_HOUR = 3600

def format_time_seconds_to_str(seconds: float) -> str:
    hours: int = int(seconds // SECS_PER_HOUR)
    minutes: int = int((seconds % SECS_PER_HOUR) // SECS_PER_MIN)
    remaining_seconds: float = seconds % SECS_PER_MIN
    return f"{hours:03d}:{minutes:02d}:{remaining_seconds:02.0f}"

def chunked(iterator: Iterator[str], size: int) -> Iterator[list[str]]:
    """Yield successive chunks of `size` lines from an iterator."""
    while True:
        chunk = list(itertools.islice(iterator, size))
        if not chunk:
            break
        yield chunk

def url_to_local_path(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme == 'file':
        # Combine netloc and path (for local files, netloc is often empty on Unix)
        if parsed.netloc and parsed.path:
            path = f"/{parsed.netloc}{parsed.path}"
        elif parsed.netloc:
            path = parsed.netloc
        else:
            path = parsed.path
        return urllib.parse.unquote(path)
    raise ValueError(f"Not a file:// URL: {url}")

def get_lines_from_url(url_or_path: str) -> Iterator[str]:
    if url_or_path.startswith("file://"):
        path = url_to_local_path(url_or_path)
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                yield line.rstrip('\n')
    else:
        response = requests.get(url_or_path, stream=True)
        response.raise_for_status()
        for line in response.iter_lines(decode_unicode=True):
            yield line

def get_line_chunks_from_url(url: str, chunk_size: int) -> Iterator[list[str]]:
    lines = get_lines_from_url(url)
    return chunked(lines, chunk_size)


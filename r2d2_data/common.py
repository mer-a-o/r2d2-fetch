"""Shared date, configuration, and filename helpers."""

import json
import os
from datetime import datetime, timedelta
from typing import Iterable

R2D2_DB = os.environ.get("R2D2_DB", "/css/jcsda/s2127/r2d2-experiments-nccs/")
_DATE_FORMATS = (
    "%Y%m%dT%H%M%S%z", "%Y%m%dT%H%M%SZ", "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H%M%SZ",
)


def parse_date(value: str) -> datetime:
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    raise ValueError(f"Unrecognized date format: {value!r}")


def parse_interval(value: str) -> timedelta:
    if not value.startswith("PT"):
        raise ValueError(f"Interval must start with 'PT': {value!r}")
    hours = minutes = seconds = 0
    number = ""
    for char in value[2:]:
        if char.isdigit():
            number += char
        elif char in "HMS":
            amount = int(number or 0)
            if char == "H": hours = amount
            elif char == "M": minutes = amount
            else: seconds = amount
            number = ""
        else:
            raise ValueError(f"Bad interval token {char!r} in {value!r}")
    result = timedelta(hours=hours, minutes=minutes, seconds=seconds)
    if result.total_seconds() <= 0:
        raise ValueError("interval must be positive")
    return result


def daterange(start: datetime, end: datetime, interval: timedelta) -> Iterable[datetime]:
    current = start
    while current <= end:
        yield current
        current += interval


def fmt_date(value: datetime) -> str:
    return value.strftime("%Y%m%dT%H%M%SZ")


def drop_none(**kwargs) -> dict:
    return {key: value for key, value in kwargs.items() if value is not None}


def is_broken_symlink(path: str) -> bool:
    return os.path.islink(path) and not os.path.exists(path)


def indexed_disk_path(item: str, date: str, index: str, extension: str = "nc") -> str:
    return os.path.join(R2D2_DB, item, date, f"{index}.{extension}")


def target_filename(item: str, *, experiment=None, model=None, resolution=None,
                    date=None, step=None, file_type=None, observation_type=None,
                    provider=None, window_start=None, member=None,
                    file_extension="nc") -> str:
    def text(value):
        return str(value) if value is not None else None

    if item == "forecast":
        parts = ["fc", experiment, model, resolution, fmt_date(date) if date else None,
                 step, file_type]
        if member is not None and str(member) not in ("-9999", "None"):
            parts.append(f"m{member}")
    elif item == "analysis":
        parts = ["an", experiment, model, resolution, fmt_date(date) if date else None, file_type]
    elif item == "feedback":
        parts = ["fb", observation_type, resolution, fmt_date(window_start) if window_start else None]
    elif item == "observation":
        parts = ["obs", observation_type, provider, fmt_date(window_start) if window_start else None]
    else:
        parts = [item, experiment, model, resolution, fmt_date(date) if date else None, file_type]
    return ".".join(text(part) for part in parts if part is not None and text(part)) + f".{file_extension}"


def load_config(path: str) -> dict:
    if path.endswith((".yaml", ".yml")):
        try:
            import yaml
        except ImportError as exc:
            raise RuntimeError("YAML support requires the 'yaml' extra: pip install r2d2-data[yaml]") from exc
        with open(path, encoding="utf-8") as stream:
            data = yaml.safe_load(stream)
    else:
        with open(path, encoding="utf-8") as stream:
            data = json.load(stream)
    if not isinstance(data, dict):
        raise ValueError(f"Config {path} must contain a mapping")
    return data

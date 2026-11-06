#!/usr/bin/env python3
"""Fetch one or more R2D2 item types over a range of cycles.

Run this file directly after loading the NASA/NCCS r2d2-client environment.
Only one entry in ITEM_CONFIGS should be uncommented at a time.
"""

from datetime import datetime, timedelta
from itertools import product
from pathlib import Path
import logging

import r2d2

from r2d2_data.common import fmt_date, parse_date, parse_interval, target_filename


# ============================================================
# Configuration
# ============================================================

START_DATE = "2025-04-11T03:00:00Z"
END_DATE = "2025-04-12T03:00:00Z"
CYCLE_INTERVAL = "PT6H"
ACTION = "fetch"                 # "search" or "fetch"

# Uncomment exactly one item section. Values may be scalars or lists. Lists
# cause the runner to fetch every combination for every cycle.
ITEM_CONFIGS = {
    # "forecast": {
    #     "model": "geos_cf",
    #     "experiment": "oper",
    #     "resolution": "c90",
    #     "steps": ["PT3H", "PT9H"],
    #     "file_type": "bkg",
    #     "member": -9999,
    #     "file_extension": "nc",
    #     "output_dir": "forecasts",
    # },
    # "analysis": {
    #     "model": "geos_cf",
    #     "experiment": "oper",
    #     "resolution": "c90",
    #     "file_type": "anl",
    #     "member": -9999,
    #     "file_extension": "nc",
    #     "output_dir": "analysis",
    # },
    "feedback": {
        "experiment": "cfv3_3dvar_cycle",
        "observation_types": ["tropomi_s5p_no2_tropo"],
        "window_length": "PT6H",
        "member": -9999,
        "file_extension": "nc4",
        "output_dir": "feedback",
    },
    # "observation": {
    #     "observation_types": ["tempo_no2_tropo"],
    #     "providers": ["nasa-v4"],
    #     "window_length": "PT6H",
    #     "file_extension": "nc4",
    #     "output_dir": "observations",
    # },
}


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)


def _values(config, plural_key, singular_key):
    """Return a configured scalar/list as a list for Cartesian iteration."""
    value = config.get(plural_key, config.get(singular_key))
    if value is None:
        return [None]
    return value if isinstance(value, (list, tuple)) else [value]


def _combinations(item, config):
    if item == "forecast":
        keys = ("steps", "step")
    elif item == "observation":
        keys = ("observation_types", "observation_type"), ("providers", "provider")
    elif item == "feedback":
        keys = (("observation_types", "observation_type"),)
    else:
        return [({},)]

    groups = [_values(config, *key) for key in keys] if item != "forecast" else [
        _values(config, *keys)
    ]
    combinations = []
    for values in product(*groups):
        if item == "forecast":
            combinations.append(({"step": values[0]},))
        elif item == "observation":
            combinations.append(({
                "observation_type": values[0],
                "provider": values[1],
            },))
        else:
            combinations.append(({"observation_type": values[0]},))
    return combinations


def _required(item, config):
    required = {
        "forecast": ("model", "experiment", "resolution", "steps"),
        "analysis": ("model", "experiment", "resolution"),
        "feedback": ("experiment", "observation_types", "window_length"),
        "observation": ("observation_types", "providers", "window_length"),
    }[item]
    missing = [key for key in required if not config.get(key)]
    # Accept singular spellings as well as the list-oriented spellings used
    # by the example configuration.
    if "steps" in missing and config.get("step"):
        missing.remove("steps")
    if "observation_types" in missing and config.get("observation_type"):
        missing.remove("observation_types")
    if "providers" in missing and config.get("provider"):
        missing.remove("providers")
    if item in ("feedback", "observation") and not _values(
            config, "observation_types", "observation_type")[0]:
        if "observation_types" not in missing:
            missing.append("observation_types")
    if item == "observation" and not _values(config, "providers", "provider")[0]:
        if "providers" not in missing:
            missing.append("providers")
    if missing:
        raise ValueError(f"{item} configuration is missing: {', '.join(missing)}")


def _r2d2_kwargs(item, config, combination, cycle):
    kwargs = {
        "item": item,
        "file_extension": config.get("file_extension", "nc4" if item in (
            "feedback", "observation") else "nc"),
    }
    kwargs.update({
        key: value for key, value in config.items()
        if key not in {"steps", "step", "observation_types", "observation_type",
                       "providers", "provider", "output_dir", "file_extension"}
    })
    kwargs.update(combination)
    if item in ("feedback", "observation"):
        kwargs["window_start"] = fmt_date(cycle)
    else:
        kwargs["date"] = fmt_date(cycle)
    return kwargs


def main():
    active = list(ITEM_CONFIGS.items())
    if len(active) != 1:
        raise ValueError("Uncomment exactly one item section in ITEM_CONFIGS")

    item, config = active[0]
    if item not in {"forecast", "analysis", "feedback", "observation"}:
        raise ValueError(f"Unsupported item: {item}")
    if ACTION not in {"search", "fetch"}:
        raise ValueError("ACTION must be either 'search' or 'fetch'")
    _required(item, config)

    start = parse_date(START_DATE)
    end = parse_date(END_DATE)
    if end < start:
        raise ValueError("END_DATE must be greater than or equal to START_DATE")
    interval = parse_interval(CYCLE_INTERVAL)
    extension = config.get("file_extension", "nc4" if item in (
        "feedback", "observation") else "nc")
    output_dir = Path(config.get("output_dir", item))
    output_dir.mkdir(parents=True, exist_ok=True)

    attempted = successful = 0
    failed = []
    cycle = start
    while cycle <= end:
        for (combination,) in _combinations(item, config):
            kwargs = _r2d2_kwargs(item, config, combination, cycle)
            if ACTION == "fetch":
                target_name = target_filename(
                    item,
                    experiment=config.get("experiment"),
                    model=config.get("model"),
                    resolution=config.get("resolution"),
                    date=cycle if item in ("forecast", "analysis") else None,
                    step=combination.get("step"),
                    file_type=config.get("file_type"),
                    observation_type=combination.get("observation_type"),
                    provider=combination.get("provider"),
                    window_start=cycle if item in ("feedback", "observation") else None,
                    member=config.get("member"),
                    file_extension=extension,
                )
                target = output_dir / target_name
                kwargs["target_file"] = str(target)
            attempted += 1
            logging.info("[%d] %s %s at %s", attempted, ACTION, item,
                         fmt_date(cycle))
            try:
                if ACTION == "fetch":
                    r2d2.fetch(**kwargs)
                else:
                    results = r2d2.search(**kwargs)
                    logging.info("Found %d result(s): %s", len(results), results)
                successful += 1
            except Exception as exc:
                logging.exception("%s failed for %s", ACTION, kwargs)
                failed.append((str(kwargs), str(exc)))
        cycle += interval

    logging.info("Completed: %d attempted, %d successful, %d failed",
                 attempted, successful, len(failed))
    if failed:
        failure_file = output_dir / f"failed_{ACTION}s.txt"
        failure_file.write_text(
            "".join(f"{target},{error}\n" for target, error in failed),
            encoding="utf-8",
        )
        logging.warning("Failure details saved to %s", failure_file)


if __name__ == "__main__":
    main()

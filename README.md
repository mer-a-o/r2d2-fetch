# R2D2 Fetch

Standalone search and fetch runner for R2D2 data over a range of dates or
assimilation windows. It calls the site-provided `r2d2` client directly and
does not require the `r2d2-data` command-line package.

## Setup

Load the R2D2 client environment before running the tool. The example module
script can be adapted for your environment:

```bash
source load_modules_example.sh
```

## Configure and run

Edit `cycle_runner.py`:

1. Set `START_DATE`, `END_DATE`, and `CYCLE_INTERVAL`.
2. Set `ACTION` to `"search"` or `"fetch"`.
3. Uncomment exactly one item section in `ITEM_CONFIGS`.
4. Fill in that item's R2D2 parameters.

Then run:

```bash
python cycle_runner.py
```

The runner uses `date` for forecasts and analyses, and `window_start` for
feedback and observations. Fetches are written to the configured
`output_dir`; failures are recorded in that directory.

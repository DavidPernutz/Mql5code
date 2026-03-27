# tradlint

tradlint is a static linter/auditor for trading bot source code, starting with MQL4/MQL5 Expert Advisors.

## What it does
- Finds live-readiness risks
- Flags fragile time/session logic
- Detects missing guards and stop checks
- Improves maintainability reviews

## What it does NOT do
- It does not predict profitability
- It does not estimate profit factor
- It does not replace backtesting or forward testing

## Install

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -e .
```

## Usage

```bash
tradlint scan path/to/file.mq5
tradlint scan path/to/file.mq5 --format json
tradlint scan path/to/bots --recursive --fail-on warning
tradlint explain MQL001
```

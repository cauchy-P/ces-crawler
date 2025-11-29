# CES Exhibitor Crawler

Python script to pull CES exhibitor search results (the same data shown on `https://exhibitors.ces.tech/8_0/#/searchtype/keyword/search/<keyword>/show/all`) and save them to CSV.

## Requirements
- Python 3.8+
- `requests` (`pip install requests`)
- Outbound HTTPS access to `https://exhibitors.ces.tech`

## Usage
Basic run (prompts for keyword if omitted):
```bash
python ai_studio_code.py
```

Explicit keyword and output file:
```bash
python ai_studio_code.py --keyword "mobility" --output exhibitors_mobility.csv
```

Adjust page size or search section (defaults shown):
```bash
python ai_studio_code.py --keyword "healthcare" --page-size 200 --show exhibitor
```

Outputs a CSV with columns:
`exhibitor_id, name, booths, hall, description, seeking_funding, funding_amount, investment_stage, revenue, logo_file, featured, tags`.

## How it works
- Boots a session against `https://exhibitors.ces.tech/8_0/` to get required cookies.
- Calls `/ajax/remote-proxy.cfm?action=search` with the given keyword and paginates until all hits are fetched.
- Writes normalized exhibitor fields to CSV.

## Notes
- If your network blocks GitHub or the CES domain, set the proper proxy in your shell before running.
- Large keywords can return hundreds of records; increase `--page-size` if needed to reduce request count.

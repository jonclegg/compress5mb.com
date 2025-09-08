### Media upload test plan

This suite generates synthetic images and videos up to 200MB, uploads them via the deployed HTTP API, polls for processing completion, and emits a JSON report with durations and success/failure.

#### Prerequisites
- ffmpeg and ffprobe available on PATH
- curl available
- Python 3.10+

#### Configure
- Set `API_BASE` environment variable to your deployed base URL (default points to current dev):

```bash
export API_BASE="https://7hme1ull8j.execute-api.us-east-1.amazonaws.com"
```

#### Run

```bash
python /Users/jonathanclegg/dev/5mb/tests/generate_and_upload.py
```

Artifacts and the final `report.json` will be written to `tests/artifacts`. The script prints the absolute path to the JSON report on completion.



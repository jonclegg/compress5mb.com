import os
import json
import base64
import uuid

import boto3

BUCKET_NAME = os.environ["BUCKET_NAME"]
s3 = boto3.client("s3")


INDEX_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>5MB Converter</title>
  <meta name="theme-color" content="#0f172a" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
  <style>
    :root {
      --bg: #0b1220;
      --bg-soft: #0f172a;
      --surface: #0f172a;
      --surface-2: #111827;
      --text: #e5e7eb;
      --muted: #94a3b8;
      --primary: #3b82f6;
      --primary-2: #2563eb;
      --primary-hover: #1d4ed8;
      --border: rgba(148, 163, 184, 0.15);
      --accent: #22d3ee;
      --success: #34d399;
      --error: #f87171;
      --radius: 16px;
      --shadow: 0 10px 30px rgba(2, 6, 23, 0.45);
    }
    @media (prefers-color-scheme: light) {
      :root {
        --bg: #f7f8fb;
        --bg-soft: #ffffff;
        --surface: #ffffff;
        --surface-2: #f9fafb;
        --text: #0f172a;
        --muted: #64748b;
        --primary: #2563eb;
        --primary-2: #1d4ed8;
        --primary-hover: #1e40af;
        --border: rgba(15, 23, 42, 0.08);
        --accent: #06b6d4;
        --success: #065f46;
        --error: #7f1d1d;
        --shadow: 0 18px 40px rgba(2, 6, 23, 0.08);
      }
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
      color: var(--text);
      background:
        radial-gradient(1000px 600px at 15% -10%, rgba(59,130,246,0.18), transparent 60%),
        radial-gradient(900px 600px at 110% 10%, rgba(34,211,238,0.16), transparent 60%),
        linear-gradient(180deg, var(--bg), var(--bg-soft));
      min-height: 100vh;
      display: grid;
      grid-template-rows: auto 1fr auto;
    }
    header { padding: 28px; text-align: center; }
    header h1 { margin: 0; font-size: 32px; letter-spacing: -0.02em; font-weight: 800; }
    header p { margin: 8px 0 0 0; color: var(--muted); }

    .container { max-width: 900px; margin: 0 auto; padding: 16px 24px 48px; width: 100%; }

    .card {
      position: relative;
      background: linear-gradient(180deg, var(--surface), var(--surface-2));
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 28px;
      box-shadow: var(--shadow);
      backdrop-filter: saturate(120%) blur(2px);
    }

    .dropzone {
      position: relative;
      display: grid;
      place-items: center;
      text-align: center;
      border: 1.5px dashed rgba(148,163,184,0.35);
      border-radius: calc(var(--radius) - 6px);
      padding: 40px;
      min-height: 230px;
      background:
        radial-gradient(500px 160px at 50% -30%, rgba(34,211,238,0.10), transparent 70%),
        linear-gradient(180deg, rgba(148,163,184,0.05), transparent 70%);
      transition: border-color 180ms ease, background 180ms ease, box-shadow 180ms ease, transform 180ms ease;
      cursor: pointer;
      outline: none;
    }
    .dropzone:hover { transform: translateY(-1px); }
    .dropzone.drag {
      border-color: var(--accent);
      background:
        radial-gradient(500px 160px at 50% -30%, rgba(34,211,238,0.18), transparent 70%),
        linear-gradient(180deg, rgba(148,163,184,0.08), transparent 70%);
      box-shadow: 0 0 0 6px rgba(34, 211, 238, 0.08) inset;
    }
    .dz-icon { color: #a7b2c3; margin-bottom: 10px; }
    .dz-title { font-size: 21px; margin: 8px 0 4px; font-weight: 600; }
    .dz-hint { color: var(--muted); margin: 0; }
    .accept { font-size: 12px; color: var(--muted); margin-top: 12px; }

    .actions { display: flex; align-items: center; gap: 12px; margin-top: 18px; }
    .filename {
      color: var(--muted);
      white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
      max-width: 60ch;
      padding: 6px 10px;
      border-radius: 999px;
      border: 1px solid var(--border);
      background: rgba(148,163,184,0.10);
    }

    .btn {
      appearance: none;
      padding: 12px 16px;
      border-radius: 12px;
      border: 1px solid rgba(255,255,255,0.06);
      background: linear-gradient(180deg, var(--primary), var(--primary-2));
      color: #fff;
      font-weight: 700;
      letter-spacing: 0.01em;
      cursor: pointer;
      transition: transform 120ms ease, filter 120ms ease, opacity 120ms ease, box-shadow 120ms ease;
      box-shadow: 0 8px 20px rgba(37,99,235,0.25);
    }
    .btn:disabled { opacity: 0.6; cursor: not-allowed; box-shadow: none; }
    .btn:not(:disabled):hover { filter: brightness(1.03); transform: translateY(-1px); }
    .btn.secondary { background: transparent; color: var(--text); border: 1px solid var(--border); box-shadow: none; }
    .btn.secondary:hover { background: rgba(148,163,184,0.10); }

    .progress-wrap { margin-top: 16px; }
    .progress { height: 12px; width: 100%; background: rgba(148,163,184,0.15); border-radius: 999px; border: 1px solid var(--border); overflow: hidden; }
    .progress-fill {
      height: 100%; width: 0%;
      background: linear-gradient(90deg, var(--accent), var(--primary));
      transition: width 150ms ease;
      background-size: 200% 100%;
    }
    .progress-fill.animated { animation: progressStripes 1.2s linear infinite; }
    @keyframes progressStripes { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
    .status-line { margin-top: 8px; display: flex; justify-content: space-between; color: var(--muted); font-size: 14px; }

    .result { display: grid; gap: 12px; margin-top: 18px; align-items: center; grid-template-columns: 1fr auto auto; }
    .link-button {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 12px 14px;
      border-radius: 12px;
      border: 1px solid rgba(255,255,255,0.06);
      background: linear-gradient(180deg, #06b6d4, #0891b2);
      color: #fff;
      text-decoration: none;
      font-weight: 700;
      box-shadow: 0 10px 24px rgba(8,145,178,0.28);
    }
    .muted { color: var(--muted); }
    .success { color: var(--success); font-weight: 600; }
    .error { color: var(--error); font-weight: 600; }
    .hidden { display: none; }

    footer { padding: 24px; text-align: center; color: var(--muted); font-size: 13px; }
  </style>
</head>
<body>
  <header>
    <h1>Convert media in seconds</h1>
    <p class="muted">Drop an image or video. We’ll handle the rest.</p>
  </header>

  <main class="container">
    <section class="card">
      <div id="dropzone" class="dropzone" tabindex="0" role="button" aria-label="Drop a file or click to choose">
        <svg class="dz-icon" width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
          <path d="M12 16V4m0 0l-4 4m4-4l4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M20 16.5a3.5 3.5 0 01-3.5 3.5h-9A3.5 3.5 0 014 16.5 3.5 3.5 0 017.5 13h.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <p class="dz-title">Drop a file here</p>
        <p class="dz-hint">or click to choose from your computer</p>
        <p class="accept">Images and videos supported</p>
        <input id="file" type="file" accept="image/*,video/*" hidden />
      </div>

      <div class="actions">
        <button id="convert" class="btn" disabled>Convert</button>
        <span id="filename" class="filename"></span>
      </div>

      <div class="progress-wrap hidden" id="progressWrap">
        <div class="progress"><div id="progressFill" class="progress-fill"></div></div>
        <div class="status-line">
          <span id="status" class="muted">Waiting</span>
          <span id="percent" class="muted">0%</span>
        </div>
      </div>

      <div id="resultWrap" class="result hidden">
        <span id="readyText" class="success">Your file is ready.</span>
        <a id="downloadLink" class="link-button" href="#" download>Download</a>
        <button id="copyLink" class="btn secondary hidden">Copy link</button>
      </div>
    </section>
  </main>

  <footer>
    <span>Max speed. Minimal fuss.</span>
  </footer>

<script>
const CHUNK_SIZE = 10 * 1024 * 1024; // 10MB per part
const TARGET_BYTES = 5 * 1024 * 1024; // 5MB size threshold

function byId(id) { return document.getElementById(id); }

function setStatus(text, cls) {
  const el = byId('status');
  el.textContent = text;
  if (cls) el.className = cls;
}

function setProgress(percent) {
  const pct = Math.max(0, Math.min(100, percent));
  byId('progressFill').style.width = pct + '%';
  byId('percent').textContent = pct + '%';
}

function formatBytes(bytes) {
  const units = ['B', 'KB', 'MB', 'GB'];
  const i = bytes > 0 ? Math.floor(Math.log(bytes) / Math.log(1024)) : 0;
  const val = bytes / Math.pow(1024, i);
  return (i === 0 ? bytes : val.toFixed(1)) + ' ' + units[i];
}

async function initiateMultipart(filename, contentType) {
  const res = await fetch('/api/multipart/initiate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filename, contentType })
  });
  if (!res.ok) throw new Error('Failed to initiate');
  return res.json();
}

async function getPresignedPartUrl(key, uploadId, partNumber) {
  const params = new URLSearchParams({ key, uploadId, partNumber: String(partNumber) });
  const res = await fetch(`/api/multipart/url?${params.toString()}`, { method: 'GET' });
  if (!res.ok) throw new Error('Failed to get URL');
  return res.json();
}

async function completeMultipart(key, uploadId, parts) {
  const res = await fetch('/api/multipart/complete', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ key, uploadId, parts })
  });
  if (!res.ok) throw new Error('Failed to complete');
  return res.json();
}

async function checkStatus(key) {
  const params = new URLSearchParams({ key });
  const res = await fetch(`/api/status?${params.toString()}`, { method: 'GET' });
  if (!res.ok) throw new Error('Failed to check status');
  return res.json();
}

function getNumParts(size, chunkSize) { return Math.ceil(size / chunkSize); }

function setSelectedFile(file) {
  if (!file) return;
  window.__selectedFile = file;
  byId('filename').textContent = file.name + ' · ' + formatBytes(file.size);
  byId('convert').disabled = false;
}

async function uploadAndProcess() {
  const file = window.__selectedFile;
  if (!file) return;

  // Early exit if file already <= 5MB
  if (file.size <= TARGET_BYTES) {
    setStatus('Already under 5 MB — no conversion needed.', 'success');
    const blobUrl = URL.createObjectURL(file);
    const link = byId('downloadLink');
    link.href = blobUrl;
    link.download = file.name;
    byId('resultWrap').classList.remove('hidden');
    setProgress(100);
    return;
  }

  byId('convert').disabled = true;
  byId('progressWrap').classList.remove('hidden');
  byId('progressFill').classList.add('animated');
  setStatus('Starting upload...', 'muted');
  setProgress(0);

  const { uploadId, key } = await initiateMultipart(file.name, file.type || 'application/octet-stream');

  const numParts = getNumParts(file.size, CHUNK_SIZE);
  const etags = [];

  for (let partNumber = 1; partNumber <= numParts; partNumber++) {
    const start = (partNumber - 1) * CHUNK_SIZE;
    const end = Math.min(start + CHUNK_SIZE, file.size);
    const blob = file.slice(start, end);

    setStatus(`Uploading ${partNumber}/${numParts}...`, 'muted');
    const { url } = await getPresignedPartUrl(key, uploadId, partNumber);
    const putRes = await fetch(url, { method: 'PUT', body: blob });
    if (!putRes.ok) throw new Error(`Part ${partNumber} failed`);

    const etag = putRes.headers.get('ETag');
    etags.push({ ETag: etag, PartNumber: partNumber });
    setProgress(Math.round((partNumber / numParts) * 100));
  }

  setStatus('Finalizing...', 'muted');
  await completeMultipart(key, uploadId, etags);

  setStatus('Processing...', 'muted');

  const pollStart = Date.now();
  const maxMs = 15 * 60 * 1000;
  const intervalMs = 3000;
  while (Date.now() - pollStart < maxMs) {
    const status = await checkStatus(key);
    if (status.ready) {
      setStatus('Done', 'success');
      byId('progressFill').classList.remove('animated');
      byId('downloadLink').href = status.url;
      const sizeText = status.size ? ' · ' + formatBytes(status.size) : '';
      byId('readyText').textContent = 'Your file is ready' + sizeText + '.';
      const copyBtn = byId('copyLink');
      copyBtn.classList.remove('hidden');
      copyBtn.onclick = () => navigator.clipboard.writeText(status.url);
      byId('resultWrap').classList.remove('hidden');
      return;
    }
    await new Promise(r => setTimeout(r, intervalMs));
  }
  setStatus('Timed out waiting for output', 'error');
}

// Wiring
const dropzone = byId('dropzone');
const fileInput = byId('file');

dropzone.addEventListener('click', () => fileInput.click());
dropzone.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') fileInput.click(); });
dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.classList.add('drag'); });
dropzone.addEventListener('dragleave', () => dropzone.classList.remove('drag'));
dropzone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropzone.classList.remove('drag');
  const f = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
  if (f) setSelectedFile(f);
});

fileInput.addEventListener('change', () => {
  const f = fileInput.files && fileInput.files[0];
  if (f) setSelectedFile(f);
});

byId('convert').addEventListener('click', () => {
  uploadAndProcess().catch(err => {
    setStatus(err && err.message ? err.message : String(err), 'error');
    byId('convert').disabled = false;
  });
});
</script>
</body>
</html>
"""


def _response(status_code, body, content_type="application/json"):
	if isinstance(body, (dict, list)):
		body_str = json.dumps(body)
	else:
		body_str = body
	headers = {
		"Content-Type": content_type,
		"Access-Control-Allow-Origin": "*",
		"Access-Control-Allow-Headers": "*",
	}
	return {"statusCode": status_code, "headers": headers, "body": body_str}

###############################################################################

def _parse_json_body(event):
	body = event.get("body")
	if not body:
		return {}
	if event.get("isBase64Encoded"):
		decoded = base64.b64decode(body)
		return json.loads(decoded)
	return json.loads(body)

###############################################################################

def _get_method_path(event):
	ctx = event.get("requestContext", {})
	http = ctx.get("http", {})
	method = http.get("method", "GET")
	path = event.get("rawPath", "/")
	return method, path

###############################################################################

def _handle_index():
	return _response(200, INDEX_HTML, content_type="text/html; charset=utf-8")

###############################################################################

def _handle_initiate(event):
	data = _parse_json_body(event)
	filename = data.get("filename")
	content_type = data.get("contentType", "application/octet-stream")
	if not filename:
		return _response(400, {"error": "filename is required"})
	key = f"uploads/{uuid.uuid4()}-{filename}"
	create = s3.create_multipart_upload(Bucket=BUCKET_NAME, Key=key, ContentType=content_type)
	upload_id = create["UploadId"]
	return _response(200, {"uploadId": upload_id, "key": key})

###############################################################################

def _handle_part_url(event):
	params = event.get("queryStringParameters") or {}
	key = params.get("key")
	upload_id = params.get("uploadId")
	part_number_raw = params.get("partNumber")
	if not key or not upload_id or not part_number_raw:
		return _response(400, {"error": "key, uploadId and partNumber are required"})
	part_number = int(part_number_raw)
	url = s3.generate_presigned_url(
		ClientMethod="upload_part",
		Params={
			"Bucket": BUCKET_NAME,
			"Key": key,
			"UploadId": upload_id,
			"PartNumber": part_number,
		},
		ExpiresIn=3600,
	)
	return _response(200, {"url": url})

###############################################################################

def _handle_complete(event):
	data = _parse_json_body(event)
	key = data.get("key")
	upload_id = data.get("uploadId")
	parts = data.get("parts") or []
	if not key or not upload_id or not parts:
		return _response(400, {"error": "key, uploadId and parts are required"})
	# Ensure parts are sorted by PartNumber ascending
	parts_sorted = sorted(parts, key=lambda p: int(p["PartNumber"]))
	result = s3.complete_multipart_upload(
		Bucket=BUCKET_NAME,
		Key=key,
		MultipartUpload={"Parts": parts_sorted},
		UploadId=upload_id,
	)
	return _response(200, result)

###############################################################################

def _handle_status(event):
	params = event.get("queryStringParameters") or {}
	key = params.get("key")
	if not key:
		return _response(400, {"error": "key is required"})

	# map uploads/<uuid>-<name.ext> -> processed/<name>.(mp4|jpg)
	base, _sep, filename = key.rpartition("/")
	name_no_ext = filename.rsplit(".", 1)[0]

	# Try both video and image outputs
	possible = [
		f"processed/{name_no_ext}.mp4",
		f"processed/{name_no_ext}.jpg",
	]

	for out_key in possible:
		try:
			head = s3.head_object(Bucket=BUCKET_NAME, Key=out_key)
			url = s3.generate_presigned_url(
				ClientMethod="get_object",
				Params={"Bucket": BUCKET_NAME, "Key": out_key},
				ExpiresIn=3600,
			)
			return _response(200, {
				"ready": True,
				"outputKey": out_key,
				"contentType": head.get("ContentType"),
				"size": int(head.get("ContentLength") or 0),
				"url": url,
			})
		except Exception:
			# not found, continue checking next possible key
			continue

	# If processed output not found, but original upload exists and is already <= 5MB, return it
	try:
		orig_head = s3.head_object(Bucket=BUCKET_NAME, Key=key)
		orig_size = int(orig_head.get("ContentLength") or 0)
		if orig_size <= 5 * 1024 * 1024:
			orig_url = s3.generate_presigned_url(
				ClientMethod="get_object",
				Params={"Bucket": BUCKET_NAME, "Key": key},
				ExpiresIn=3600,
			)
			return _response(200, {
				"ready": True,
				"outputKey": key,
				"contentType": orig_head.get("ContentType"),
				"size": orig_size,
				"url": orig_url,
				"note": "original file already <= 5MB",
			})
	except Exception:
		pass

	return _response(200, {"ready": False})

###############################################################################

def handle(event, context):
	method, path = _get_method_path(event)
	if method == "GET" and path == "/":
		return _handle_index()
	if method == "POST" and path == "/api/multipart/initiate":
		return _handle_initiate(event)
	if method == "GET" and path == "/api/multipart/url":
		return _handle_part_url(event)
	if method == "POST" and path == "/api/multipart/complete":
		return _handle_complete(event)
	if method == "GET" and path == "/api/status":
		return _handle_status(event)
	return _response(404, {"error": "Not Found"})

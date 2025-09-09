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

    .file-info { display: grid; place-items: center; text-align: center; }
    .file-icon { color: var(--primary); margin-bottom: 12px; }
    .file-name { 
      font-size: 14px; 
      margin: 0 0 4px 0; 
      font-weight: 600; 
      color: var(--text); 
      word-break: break-all; 
      max-width: 350px; 
      line-height: 1.3;
      overflow: hidden;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
    }
    .file-size { font-size: 14px; margin: 0 0 8px 0; color: var(--muted); font-weight: 500; }
    .file-hint { font-size: 12px; color: var(--muted); margin: 0; }

    .actions { display: flex; justify-content: center; align-items: center; gap: 12px; margin-top: 18px; }
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
      padding: 20px 32px;
      border-radius: 16px;
      border: 1px solid rgba(255,255,255,0.06);
      background: linear-gradient(180deg, var(--primary), var(--primary-2));
      color: #fff;
      font-size: 18px;
      font-weight: 700;
      letter-spacing: 0.01em;
      cursor: pointer;
      transition: transform 120ms ease, filter 120ms ease, opacity 120ms ease, box-shadow 120ms ease;
      box-shadow: 0 12px 28px rgba(37,99,235,0.25);
      min-width: 200px;
    }
    .btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
      box-shadow: none;
      background: #6b7280;
      color: #d1d5db;
      filter: grayscale(100%);
    }
    .btn:not(:disabled):hover { filter: brightness(1.03); transform: translateY(-1px); }
    .btn.secondary { background: transparent; color: var(--text); border: 1px solid var(--border); box-shadow: none; }
    .btn.secondary:hover { background: rgba(148,163,184,0.10); }

    .progress-wrap { margin-top: 16px; }
    .progress { height: 12px; width: 100%; background: rgba(148,163,184,0.15); border-radius: 999px; border: 1px solid var(--border); overflow: hidden; }
    .progress-fill {
      height: 100%; width: 0%;
      background: linear-gradient(90deg, var(--accent), var(--primary));
      transition: width 300ms ease;
      background-size: 200% 100%;
    }
    .progress-fill.animated { animation: progressStripes 3s linear infinite; }
    @keyframes progressStripes { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
    .status-line { margin-top: 8px; display: flex; justify-content: space-between; color: var(--muted); font-size: 14px; }

    .result { display: flex; flex-direction: column; gap: 18px; margin-top: 18px; align-items: center; text-align: center; }
    .link-button {
      appearance: none;
      padding: 20px 32px;
      border-radius: 16px;
      border: 1px solid rgba(255,255,255,0.06);
      background: linear-gradient(180deg, #06b6d4, #0891b2);
      color: #fff;
      font-size: 18px;
      font-weight: 700;
      letter-spacing: 0.01em;
      cursor: pointer;
      transition: transform 120ms ease, filter 120ms ease, opacity 120ms ease, box-shadow 120ms ease;
      box-shadow: 0 12px 28px rgba(8,145,178,0.28);
      min-width: 200px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      text-decoration: none;
    }
    .link-button:hover { filter: brightness(1.03); transform: translateY(-1px); }
    .muted { color: var(--muted); }
    .success { color: var(--success); font-weight: 600; }
    .error { color: var(--error); font-weight: 600; }
    .hidden { display: none; }

    footer { padding: 24px; text-align: center; color: var(--muted); font-size: 13px; }
  </style>
</head>
<body>
  <header>
    <h1>Convert Any Media to Under 5 Megabytes</h1>
    <p style="margin: 8px 0 0 0; color: var(--muted); line-height: 1.6;">
      Designed specifically for school apps and platforms that have file size limits.
    </p>
    <p style="margin: 8px 0 0 0; color: var(--muted); line-height: 1.6;">
      Simply upload your file and we'll automatically compress it to meet the 5MB requirement.
    </p>
  </header>

  <main class="container">
    <section class="card">
      <label id="dropzone" for="file" class="dropzone" tabindex="0" role="button" aria-label="Drop a file or click to choose">
        <div id="dropzoneDefault">
          <svg class="dz-icon" width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <path d="M12 16V4m0 0l-4 4m4-4l4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M20 16.5a3.5 3.5 0 01-3.5 3.5h-9A3.5 3.5 0 014 16.5 3.5 3.5 0 017.5 13h.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <p class="dz-title">Drop a file here</p>
          <p class="dz-hint">or click to choose from your computer</p>
          <p class="accept">Images and videos supported</p>
        </div>
        <div id="fileInfo" class="file-info hidden">
          <svg class="file-icon" width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M14 2v6h6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <p id="fileName" class="file-name"></p>
          <p id="fileSize" class="file-size"></p>
          <p class="file-hint">Click to choose a different file</p>
        </div>
        <input id="file" type="file" accept="image/*,video/*" style="position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0;" />
      </label>

      <div class="actions">
        <button id="convert" class="btn" disabled>Convert</button>
        <a id="downloadLink" class="link-button hidden" href="#" download>Download</a>
      </div>

      <div class="progress-wrap hidden" id="progressWrap">
        <div class="progress"><div id="progressFill" class="progress-fill"></div></div>
        <div class="status-line">
          <span id="status" class="muted">Waiting</span>
          <span id="timeRemaining" class="muted hidden"></span>
          <span id="percent" class="muted">0%</span>
        </div>
      </div>

      <div id="resultWrap" class="result hidden">
        <span id="readyText" class="success">Your file is ready.</span>
        <button id="copyLink" class="btn secondary hidden">Copy link</button>
      </div>
    </section>
  </main>

  <footer>
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

function setTimeRemaining(seconds) {
  const timeEl = byId('timeRemaining');
  if (seconds > 0) {
    timeEl.textContent = formatTime(seconds) + ' remaining';
    timeEl.classList.remove('hidden');
  } else {
    timeEl.classList.add('hidden');
  }
}

function formatBytes(bytes) {
  const units = ['B', 'KB', 'MB', 'GB'];
  const i = bytes > 0 ? Math.floor(Math.log(bytes) / Math.log(1024)) : 0;
  const val = bytes / Math.pow(1024, i);
  return (i === 0 ? bytes : val.toFixed(1)) + ' ' + units[i];
}

function formatTime(seconds) {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const mins = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  return `${mins}m ${secs}s`;
}

function getDownloadFilename(status) {
  if (status.outputKey) {
    const parts = status.outputKey.split('/');
    const filename = parts[parts.length - 1];
    if (filename && filename !== '') return filename;
  }
  if (status.contentType) {
    if (status.contentType.startsWith('video/')) return 'converted-video.mp4';
    if (status.contentType.startsWith('image/')) return 'converted-image.jpg';
  }
  return 'converted-file';
}

// Indeterminate processing animation handled by CSS class 'animated'

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
  if (!file) {
    // Reset to default dropzone state
    byId('dropzoneDefault').classList.remove('hidden');
    byId('fileInfo').classList.add('hidden');
    return;
  }
  
  // Check if file exceeds 100MB limit
  const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100MB
  if (file.size > MAX_FILE_SIZE) {
    // Reset UI state
    byId('resultWrap').classList.add('hidden');
    byId('progressFill').classList.remove('animated');
    setProgress(0);
    
    // Show progress wrap so status message is visible
    byId('progressWrap').classList.remove('hidden');
    
    // Show error message
    setStatus(`File too large (${formatBytes(file.size)}). Files larger than 100MB won't compress down to 5MB and look good.`, 'error');
    
    // Keep convert button disabled
    byId('convert').disabled = true;
    window.__selectedFile = null;
    
    // Reset to default dropzone state
    byId('dropzoneDefault').classList.remove('hidden');
    byId('fileInfo').classList.add('hidden');
    return;
  }
  
  window.__selectedFile = file;
  byId('convert').disabled = false;
  
  // Show file info in dropzone
  byId('fileName').textContent = file.name;
  byId('fileSize').textContent = formatBytes(file.size);
  byId('dropzoneDefault').classList.add('hidden');
  byId('fileInfo').classList.remove('hidden');
  
  // Reset UI state when new file is selected
  byId('resultWrap').classList.add('hidden');
  byId('progressWrap').classList.add('hidden');
  byId('progressFill').classList.remove('animated');
  setProgress(0);
  setStatus('Waiting', 'muted');

  // Reset button states
  byId('convert').classList.remove('hidden');
  byId('downloadLink').classList.add('hidden');
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
    byId('convert').classList.add('hidden');
    link.classList.remove('hidden');
    byId('resultWrap').classList.remove('hidden');
    setProgress(100);
    return;
  }

  byId('convert').disabled = true;
  byId('progressWrap').classList.remove('hidden');
  setStatus('Starting upload...', 'muted');
  setProgress(0);

  const { uploadId, key } = await initiateMultipart(file.name, file.type || 'application/octet-stream');

  const numParts = getNumParts(file.size, CHUNK_SIZE);
  const etags = [];

  for (let partNumber = 1; partNumber <= numParts; partNumber++) {
    const start = (partNumber - 1) * CHUNK_SIZE;
    const end = Math.min(start + CHUNK_SIZE, file.size);
    const blob = file.slice(start, end);

    setStatus('Uploading...', 'muted');
    const { url } = await getPresignedPartUrl(key, uploadId, partNumber);
    const putRes = await fetch(url, { method: 'PUT', body: blob });
    if (!putRes.ok) throw new Error(`Part ${partNumber} failed`);

    const etag = putRes.headers.get('ETag');
    etags.push({ ETag: etag, PartNumber: partNumber });

    // Smooth progress update - calculate percentage for current chunk
    const chunkProgress = (partNumber - 1) / numParts * 100;
    const currentChunkSize = end - start;
    const totalUploaded = (partNumber - 1) * CHUNK_SIZE + currentChunkSize;
    const smoothProgress = (totalUploaded / file.size) * 100;

    setProgress(Math.round(smoothProgress));
  }

  setStatus('Finalizing...', 'muted');
  await completeMultipart(key, uploadId, etags);

  setStatus('Processing...', 'muted');

  const pollStart = Date.now();
  const maxMs = 15 * 60 * 1000;
  const intervalMs = 3000;
  
  // Indeterminate animation during processing
  byId('progressFill').classList.add('animated');
  byId('percent').classList.add('hidden');
  byId('timeRemaining').classList.add('hidden');
  setProgress(100);
  
  while (Date.now() - pollStart < maxMs) {
    const status = await checkStatus(key);
    if (status.failed) {
      byId('progressFill').classList.remove('animated');
      byId('percent').classList.remove('hidden');
      setStatus(status.error || 'Conversion failed', 'error');
      byId('convert').disabled = false;
      byId('convert').classList.remove('hidden');
      byId('downloadLink').classList.add('hidden');
      return;
    }
    if (status.ready) {
      setStatus('Done', 'success');
      byId('progressFill').classList.remove('animated');
      byId('percent').classList.remove('hidden');
      setProgress(100);
      const link = byId('downloadLink');
      const filename = getDownloadFilename(status);
      link.href = status.url;
      link.download = filename;

      // Replace convert button with download button
      byId('convert').classList.add('hidden');
      link.classList.remove('hidden');

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
  byId('progressFill').classList.remove('animated');
  byId('percent').classList.remove('hidden');
  setStatus('Timed out waiting for output', 'error');
  byId('convert').disabled = false;
  byId('convert').classList.remove('hidden');
  byId('downloadLink').classList.add('hidden');
}

// Wiring
const dropzone = byId('dropzone');
const fileInput = byId('file');

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

def _status_key_for_upload(upload_key: str) -> str:
	base, _sep, filename = upload_key.rpartition("/")
	return f"status/{filename}.json"

###############################################################################

def _write_status(upload_key: str, state: str, extra: dict | None = None):
	status_key = _status_key_for_upload(upload_key)
	payload = {"state": state, "source": upload_key}
	if extra:
		payload.update(extra)
	s3.put_object(Bucket=BUCKET_NAME, Key=status_key, Body=json.dumps(payload).encode("utf-8"), ContentType="application/json")

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
	key = f"uploads/{uuid.uuid4()}"
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
	# Record processing state so the client can display progress while Lambda runs
	_write_status(key, "processing", {"message": "awaiting conversion"})
	return _response(200, result)

###############################################################################

def _handle_status(event):
	params = event.get("queryStringParameters") or {}
	key = params.get("key")
	if not key:
		return _response(400, {"error": "key is required"})

	# First, check explicit status JSON if present
	status_key = _status_key_for_upload(key)
	try:
		obj = s3.get_object(Bucket=BUCKET_NAME, Key=status_key)
		status_payload = json.loads(obj["Body"].read())
		state = status_payload.get("state")
		if state == "failure":
			return _response(200, {"ready": False, "failed": True, "error": status_payload.get("error")})
		if state == "processing":
			return _response(200, {"ready": False, "state": "processing"})
		if state == "completed":
			out_key = status_payload.get("output")
			if out_key:
				try:
					head = s3.head_object(Bucket=BUCKET_NAME, Key=out_key)
					basename = os.path.basename(out_key)
					url = s3.generate_presigned_url(
						ClientMethod="get_object",
						Params={
							"Bucket": BUCKET_NAME,
							"Key": out_key,
							"ResponseContentDisposition": f"attachment; filename=\"{basename}\"",
						},
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
					# If for some reason the output isn't there, fall through to legacy checks
					pass
	except Exception:
		# No status file yet; fall through to legacy behavior
		pass

	# Legacy mapping: uploads/<uuid>-<name.ext> -> processed/<name>.(mp4|jpg)
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
			basename = os.path.basename(out_key)
			url = s3.generate_presigned_url(
				ClientMethod="get_object",
				Params={
					"Bucket": BUCKET_NAME,
					"Key": out_key,
					"ResponseContentDisposition": f"attachment; filename=\"{basename}\"",
				},
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
			basename = os.path.basename(key)
			orig_url = s3.generate_presigned_url(
				ClientMethod="get_object",
				Params={
					"Bucket": BUCKET_NAME,
					"Key": key,
					"ResponseContentDisposition": f"attachment; filename=\"{basename}\"",
				},
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

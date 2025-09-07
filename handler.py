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
  <title>Upload to S3 (Multipart)</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif; margin: 2rem; }
    .card { max-width: 720px; margin: 0 auto; padding: 1.5rem; border: 1px solid #e5e7eb; border-radius: 12px; }
    h1 { margin-top: 0; }
    input[type=file] { margin: 0.5rem 0 1rem 0; }
    progress { width: 100%; height: 16px; }
    .row { display: flex; gap: 0.5rem; align-items: center; }
    .muted { color: #6b7280; }
    .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
    .success { color: #065f46; }
    .error { color: #7f1d1d; }
    button { padding: 0.5rem 0.75rem; border-radius: 8px; border: 1px solid #e5e7eb; background: #111827; color: white; cursor: pointer; }
    button:disabled { opacity: 0.6; cursor: not-allowed; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Upload a file to S3</h1>
    <p class="muted">Images or videos are supported. Large files are uploaded using multipart.</p>
    <input id="file" type="file" accept="image/*,video/*" />
    <div class="row">
      <button id="upload">Upload</button>
      <span id="status" class="muted"></span>
    </div>
    <div style="margin-top: 1rem;">
      <progress id="progress" max="100" value="0"></progress>
    </div>
    <pre id="result" class="mono"></pre>
    <div id="download" style="margin-top: 1rem;"></div>
  </div>

<script>
const CHUNK_SIZE = 10 * 1024 * 1024; // 10MB per part (>= 5MB)

function byId(id) { return document.getElementById(id); }

function setStatus(text, cls = "muted") {
  const el = byId('status');
  el.textContent = text;
  el.className = cls;
}

function setProgress(percent) {
  byId('progress').value = percent;
}

async function initiateMultipart(filename, contentType) {
  const res = await fetch('/api/multipart/initiate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filename, contentType })
  });
  if (!res.ok) throw new Error('Failed to initiate multipart upload');
  return res.json();
}

async function getPresignedPartUrl(key, uploadId, partNumber) {
  const params = new URLSearchParams({ key, uploadId, partNumber: String(partNumber) });
  const res = await fetch(`/api/multipart/url?${params.toString()}`, { method: 'GET' });
  if (!res.ok) throw new Error('Failed to get presigned URL');
  return res.json();
}

async function completeMultipart(key, uploadId, parts) {
  const res = await fetch('/api/multipart/complete', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ key, uploadId, parts })
  });
  if (!res.ok) throw new Error('Failed to complete multipart upload');
  return res.json();
}

async function checkStatus(key) {
  const params = new URLSearchParams({ key });
  const res = await fetch(`/api/status?${params.toString()}`, { method: 'GET' });
  if (!res.ok) throw new Error('Failed to check status');
  return res.json();
}

function getNumParts(size, chunkSize) {
  return Math.ceil(size / chunkSize);
}

async function uploadFile() {
  const file = byId('file').files[0];
  if (!file) {
    setStatus('Please choose a file.');
    return;
  }

  byId('upload').disabled = true;
  setStatus('Initiating multipart upload...');
  setProgress(0);

  const { uploadId, key } = await initiateMultipart(file.name, file.type || 'application/octet-stream');

  const numParts = getNumParts(file.size, CHUNK_SIZE);
  const etags = [];

  for (let partNumber = 1; partNumber <= numParts; partNumber++) {
    const start = (partNumber - 1) * CHUNK_SIZE;
    const end = Math.min(start + CHUNK_SIZE, file.size);
    const blob = file.slice(start, end);

    setStatus(`Uploading part ${partNumber}/${numParts}...`);
    const { url } = await getPresignedPartUrl(key, uploadId, partNumber);

    const putRes = await fetch(url, { method: 'PUT', body: blob });
    if (!putRes.ok) {
      throw new Error(`Failed to upload part ${partNumber}`);
    }

    const etag = putRes.headers.get('ETag');
    etags.push({ ETag: etag, PartNumber: partNumber });

    const percent = Math.round((partNumber / numParts) * 100);
    setProgress(percent);
  }

  setStatus('Completing multipart upload...');
  const complete = await completeMultipart(key, uploadId, etags);

  setStatus('Upload completed', 'success');
  byId('result').textContent = JSON.stringify(complete, null, 2);
  byId('upload').disabled = false;

  // Poll for processed output
  const pollStart = Date.now();
  const maxMs = 15 * 60 * 1000; // 15 minutes
  const intervalMs = 3000;
  setStatus('Processing... waiting for output');
  const download = byId('download');
  download.textContent = '';
  while (Date.now() - pollStart < maxMs) {
    const status = await checkStatus(key);
    if (status.ready) {
      setStatus('Processing complete!', 'success');
      download.innerHTML = `<a href="${status.url}" download>Download processed file</a>`;
      byId('result').textContent = JSON.stringify(status, null, 2);
      return;
    }
    await new Promise(r => setTimeout(r, intervalMs));
  }
  setStatus('Timed out waiting for processed output', 'error');
}

byId('upload').addEventListener('click', () => {
  uploadFile().catch(err => {
    setStatus(err.message || String(err), 'error');
    byId('upload').disabled = false;
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

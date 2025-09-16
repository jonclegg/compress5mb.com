import os
import json
import base64
import uuid
import time

import boto3

BUCKET_NAME = os.environ["BUCKET_NAME"]
DYNAMO_TABLE = os.environ["DYNAMO_TABLE"]
s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")


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

    .file-list { 
      display: flex; 
      flex-direction: column; 
      gap: 12px; 
      max-height: 300px; 
      overflow-y: auto; 
      padding: 16px 0; 
    }
    .file-item { 
      display: flex; 
      align-items: center; 
      justify-content: space-between; 
      padding: 12px 16px; 
      background: rgba(148,163,184,0.08); 
      border: 1px solid var(--border); 
      border-radius: 12px; 
      transition: background 150ms ease;
    }
    .file-item:hover { background: rgba(148,163,184,0.12); }
    .file-item-info { display: flex; flex-direction: column; gap: 2px; flex: 1; }
    .file-item-name { 
      font-size: 14px; 
      font-weight: 600; 
      color: var(--text); 
      margin: 0;
      word-break: break-all;
      line-height: 1.3;
    }
    .file-item-size { 
      font-size: 12px; 
      color: var(--muted); 
      margin: 0;
    }
    .file-item-remove { 
      appearance: none; 
      background: none; 
      border: none; 
      color: var(--muted); 
      cursor: pointer; 
      padding: 4px; 
      border-radius: 4px; 
      transition: color 150ms ease, background 150ms ease;
      margin-left: 8px;
    }
    .file-item-remove:hover { 
      color: var(--error); 
      background: rgba(248,113,113,0.1); 
    }
    .files-summary { 
      text-align: center; 
      color: var(--muted); 
      font-size: 13px; 
      margin: 8px 0; 
    }

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
    .btn.with-icon { display: inline-flex; align-items: center; gap: 8px; }

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

    /* Mobile optimizations */
    @media (max-width: 768px) {
      header { padding: 20px 16px; }
      header h1 { font-size: 24px; line-height: 1.2; }
      header p { font-size: 14px; margin: 6px 0 0 0; }
      
      .container { max-width: 100%; margin: 0; padding: 12px 16px 32px; }
      
      .card { 
        padding: 20px; 
        border-radius: 12px;
        margin: 0;
      }
      
      .actions { 
        flex-direction: column; 
        gap: 12px; 
        margin-top: 20px;
        width: 100%;
      }
      
      .btn { 
        padding: 16px 24px; 
        font-size: 16px; 
        min-width: unset;
        width: 100%;
        border-radius: 12px;
      }
      
      .btn.secondary {
        margin-top: 8px;
      }
      
      .progress-wrap { margin-top: 20px; }
      .progress { height: 10px; }
      
      .status-line { 
        flex-direction: column; 
        gap: 4px; 
        text-align: center;
        font-size: 13px;
      }
      
      .dropzone { 
        padding: 24px 16px; 
        min-height: 180px;
        border-radius: 8px;
      }
      
      .dz-title { font-size: 18px; }
      .dz-hint { font-size: 14px; }
      .accept { font-size: 11px; }
      
      .file-name { 
        font-size: 13px; 
        max-width: 280px; 
        line-height: 1.4;
      }
      .file-size { font-size: 13px; }
      .file-hint { font-size: 11px; }
      
      .filename { 
        max-width: 45ch; 
        font-size: 13px;
        padding: 4px 8px;
      }
      
      .file-list { padding: 12px 0; }
      .file-item { 
        padding: 12px; 
        flex-direction: column; 
        align-items: stretch; 
        gap: 8px;
      }
      .file-item-info { gap: 4px; }
      .file-item-name { font-size: 13px; }
      .file-item-size { font-size: 11px; }
      .file-item-remove { align-self: flex-end; margin-left: 0; }
      .files-summary { font-size: 12px; }
      
      .result { gap: 16px; margin-top: 16px; }
      .link-button { 
        padding: 16px 24px; 
        font-size: 16px; 
        min-width: unset;
        width: 100%;
        border-radius: 12px;
      }
    }

    /* Extra small mobile devices */
    @media (max-width: 480px) {
      header h1 { font-size: 20px; }
      header p { font-size: 13px; }
      
      .container { padding: 8px 12px 24px; }
      .card { padding: 16px; }
      
      .dropzone { 
        padding: 20px 12px; 
        min-height: 160px;
      }
      
      .btn { 
        padding: 14px 20px; 
        font-size: 15px;
      }
      
      .file-name { max-width: 240px; }
      .filename { max-width: 35ch; font-size: 12px; }
      
      .status-line { font-size: 12px; }
    }
  </style>
</head>
<body>
  <header>
    <h1>Compress Any Media to Under 5 Megabytes</h1>
    <p style="margin: 8px 0 0 0; color: var(--muted); line-height: 1.6;">
      Designed specifically for school apps and platforms that have file size limits.
    </p>
    <p style="margin: 8px 0 0 0; color: var(--muted); line-height: 1.6;">
      Simply upload your file and we'll automatically compress it to meet the 5MB requirement or convert the format.
    </p>
  </header>

  <main class="container">
    <section id="screenStart" class="card">
      <label id="dropzone" for="file" class="dropzone" tabindex="0" role="button" aria-label="Drop a file or click to choose">
        <div id="dropzoneDefault">
          <svg class="dz-icon" width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <path d="M12 16V4m0 0l-4 4m4-4l4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M20 16.5a3.5 3.5 0 01-3.5 3.5h-9A3.5 3.5 0 014 16.5 3.5 3.5 0 017.5 13h.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <p class="dz-title">Drop files here</p>
          <p class="dz-hint">or click to choose from your computer</p>
          <p class="accept">Images and videos supported • Multiple files OK</p>
        </div>
        <div id="fileInfo" class="file-info hidden">
          <svg class="file-icon" width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M14 2v6h6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <p id="fileName" class="file-name"></p>
          <p id="fileSize" class="file-size"></p>
          <p class="file-hint">Click to choose different files</p>
        </div>
        <div id="fileList" class="file-list hidden"></div>
        <div id="filesSummary" class="files-summary hidden"></div>
        <input id="file" type="file" accept="image/*,video/*" multiple style="position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0;" />
      </label>

      <div class="actions">
        <button id="convert" class="btn" disabled>Convert</button>
      </div>
      <div id="startStatus" class="muted" style="margin-top:12px;">
        
      </div>
    </section>

    <section id="screenProcessing" class="card hidden">
      <div class="progress-wrap" id="progressWrap">
        <div class="progress"><div id="progressFill" class="progress-fill"></div></div>
        <div class="status-line">
          <span id="status" class="muted">Waiting</span>
          <span id="timeRemaining" class="muted hidden"></span>
          <span id="percent" class="muted">0%</span>
        </div>
      </div>
      <div class="actions">
        <button id="processingDownload" class="btn" disabled>Download</button>
        <button id="convertMore" class="btn secondary with-icon hidden" type="button" aria-label="Convert More (opens in a new tab)">
          Convert More
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <path d="M13 5h6m0 0v6m0-6L10 14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M20 14v5a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>
    </section>
  </main>

  <footer>
  </footer>

<script>
const CHUNK_SIZE = 10 * 1024 * 1024; // 10MB per part
const TARGET_BYTES = 5 * 1024 * 1024; // 5MB size threshold

function byId(id) { return document.getElementById(id); }

function showScreen(name) {
  const start = byId('screenStart');
  const processing = byId('screenProcessing');
  if (start) start.classList.toggle('hidden', name !== 'start');
  if (processing) processing.classList.toggle('hidden', name !== 'processing');
}

function setStatus(text, cls) {
  const el = byId('status');
  if (el) {
    el.textContent = text;
    if (cls) el.className = cls;
  }
  const elStart = byId('startStatus');
  if (elStart) {
    elStart.textContent = text;
    if (cls) elStart.className = cls;
  }
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

// Global array to store selected files
window.__selectedFiles = [];

function setSelectedFiles(files) {
  if (!files || files.length === 0) {
    // Reset to default dropzone state
    window.__selectedFiles = [];
    byId('dropzoneDefault').classList.remove('hidden');
    byId('fileInfo').classList.add('hidden');
    byId('fileList').classList.add('hidden');
    byId('filesSummary').classList.add('hidden');
    byId('convert').disabled = true;
    setStatus('', 'muted');
    return;
  }
  
  // Filter out files that are too large and show errors
  const MAX_FILE_SIZE = 200 * 1024 * 1024; // 200MB
  const validFiles = [];
  const invalidFiles = [];
  
  for (const file of files) {
    if (file.size > MAX_FILE_SIZE) {
      invalidFiles.push(file);
    } else {
      validFiles.push(file);
    }
  }
  
  if (invalidFiles.length > 0) {
    const fileNames = invalidFiles.map(f => f.name).join(', ');
    setStatus(`${invalidFiles.length} file(s) too large: ${fileNames}. Files larger than 200MB won't compress down to 5MB and look good.`, 'error');
  } else {
    setStatus('', 'muted');
  }
  
  window.__selectedFiles = validFiles;
  
  if (validFiles.length === 0) {
    byId('convert').disabled = true;
    return;
  }
  
  byId('convert').disabled = false;
  
  // Show file list
  if (validFiles.length === 1) {
    // Single file - show in original format
    const file = validFiles[0];
    byId('fileName').textContent = file.name;
    byId('fileSize').textContent = formatBytes(file.size);
    byId('dropzoneDefault').classList.add('hidden');
    byId('fileInfo').classList.remove('hidden');
    byId('fileList').classList.add('hidden');
    byId('filesSummary').classList.add('hidden');
  } else {
    // Multiple files - show as list
    byId('dropzoneDefault').classList.add('hidden');
    byId('fileInfo').classList.add('hidden');
    byId('fileList').classList.remove('hidden');
    byId('filesSummary').classList.remove('hidden');
    
    renderFileList();
  }
}

function renderFileList() {
  const fileList = byId('fileList');
  const filesSummary = byId('filesSummary');
  
  // Clear existing content
  fileList.innerHTML = '';
  
  // Render each file
  window.__selectedFiles.forEach((file, index) => {
    const fileItem = document.createElement('div');
    fileItem.className = 'file-item';
    fileItem.innerHTML = `
      <div class="file-item-info">
        <p class="file-item-name">${file.name}</p>
        <p class="file-item-size">${formatBytes(file.size)}</p>
      </div>
      <button class="file-item-remove" title="Remove file" data-index="${index}">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
    `;
    
    // Add remove functionality
    const removeBtn = fileItem.querySelector('.file-item-remove');
    removeBtn.addEventListener('click', () => {
      removeFile(index);
    });
    
    fileList.appendChild(fileItem);
  });
  
  // Update summary
  const totalSize = window.__selectedFiles.reduce((sum, file) => sum + file.size, 0);
  filesSummary.textContent = `${window.__selectedFiles.length} files selected • ${formatBytes(totalSize)} total`;
}

function removeFile(index) {
  window.__selectedFiles.splice(index, 1);
  
  if (window.__selectedFiles.length === 0) {
    setSelectedFiles([]);
  } else {
    renderFileList();
    
    // Update summary
    const totalSize = window.__selectedFiles.reduce((sum, file) => sum + file.size, 0);
    byId('filesSummary').textContent = `${window.__selectedFiles.length} files selected • ${formatBytes(totalSize)} total`;
  }
}

function addFiles(newFiles) {
  // Convert FileList to Array and combine with existing files
  const existingFiles = window.__selectedFiles || [];
  const filesToAdd = Array.from(newFiles);
  const allFiles = [...existingFiles, ...filesToAdd];
  setSelectedFiles(allFiles);
}

// Global tracking for multi-file upload
window.__activeUploads = [];

async function uploadAndProcess() {
  const files = window.__selectedFiles;
  if (!files || files.length === 0) return;

  byId('convert').disabled = true;
  showScreen('processing');
  
  // Initialize the processing screen for multiple files
  initializeMultiFileProcessing(files);
  
  // Process all files
  window.__activeUploads = files.map((file, index) => ({
    file,
    index,
    key: null,
    status: 'pending',
    error: null,
    downloadUrl: null
  }));
  
  // Upload all files sequentially
  for (let i = 0; i < files.length; i++) {
    try {
      await uploadSingleFile(i);
    } catch (error) {
      console.error(`Failed to upload file ${i}:`, error);
      updateFileStatus(i, 'failed', error.message);
    }
  }
  
  // Start polling for all uploaded files
  pollAllFiles();
}

async function uploadSingleFile(fileIndex) {
  const upload = window.__activeUploads[fileIndex];
  const file = upload.file;
  
  updateFileStatus(fileIndex, 'uploading', `Uploading...`);
  
  const { uploadId, key } = await initiateMultipart(file.name, file.type || 'application/octet-stream');
  upload.key = key;
  
  const numParts = getNumParts(file.size, CHUNK_SIZE);
  const etags = [];

  for (let partNumber = 1; partNumber <= numParts; partNumber++) {
    const start = (partNumber - 1) * CHUNK_SIZE;
    const end = Math.min(start + CHUNK_SIZE, file.size);
    const blob = file.slice(start, end);

    const { url } = await getPresignedPartUrl(key, uploadId, partNumber);
    const putRes = await fetch(url, { method: 'PUT', body: blob });
    if (!putRes.ok) throw new Error(`Part ${partNumber} failed`);

    const etag = putRes.headers.get('ETag');
    etags.push({ ETag: etag, PartNumber: partNumber });

    // Update progress for this specific file
    const progress = Math.round((partNumber / numParts) * 100);
    updateFileProgress(fileIndex, progress);
    
    // For single file, also update the main progress bar
    if (window.__selectedFiles.length === 1) {
      setProgress(progress);
      setStatus('Uploading...', 'muted');
    }
  }

  await completeMultipart(key, uploadId, etags);
  updateFileStatus(fileIndex, 'processing', 'Processing...');
  
  // For single file, update main status
  if (window.__selectedFiles.length === 1) {
    setStatus('Processing...', 'muted');
    setProgress(100);
    byId('progressFill').classList.add('animated');
    byId('percent').classList.add('hidden');
  }
}

function initializeMultiFileProcessing(files) {
  if (files.length === 1) {
    // Single file - use enhanced single file display with filename
    initializeSingleFileProcessing(files[0]);
    return;
  }
  
  // Multiple files - show list
  byId('progressWrap').classList.add('hidden');
  
  // Create the multi-file status area
  const processing = byId('screenProcessing');
  
  // Find existing multiFileStatus or create it
  let multiFileStatus = byId('multiFileStatus');
  if (!multiFileStatus) {
    multiFileStatus = document.createElement('div');
    multiFileStatus.id = 'multiFileStatus';
    multiFileStatus.innerHTML = '<h3 style="margin: 0 0 16px 0; color: var(--text);">Processing Files</h3>';
    
    // Insert it before the actions div
    const actions = processing.querySelector('.actions');
    processing.insertBefore(multiFileStatus, actions);
  }
  
  // Clear and rebuild the file status list
  const existingList = multiFileStatus.querySelector('.file-status-list');
  if (existingList) existingList.remove();
  
  const fileStatusList = document.createElement('div');
  fileStatusList.className = 'file-status-list';
  fileStatusList.style.cssText = 'display: flex; flex-direction: column; gap: 12px; margin-bottom: 24px;';
  
  files.forEach((file, index) => {
    const fileStatus = document.createElement('div');
    fileStatus.className = 'file-status-item';
    fileStatus.id = `fileStatus${index}`;
    fileStatus.style.cssText = 'padding: 16px; background: rgba(148,163,184,0.08); border: 1px solid var(--border); border-radius: 12px;';
    
    fileStatus.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <span style="font-weight: 600; color: var(--text); font-size: 14px;">${file.name}</span>
        <span id="fileStatusText${index}" style="color: var(--muted); font-size: 12px;">Waiting</span>
      </div>
      <div style="height: 8px; background: rgba(148,163,184,0.15); border-radius: 4px; overflow: hidden;">
        <div id="fileProgress${index}" style="height: 100%; width: 0%; background: linear-gradient(90deg, var(--accent), var(--primary)); transition: width 300ms ease;"></div>
      </div>
      <div id="fileDownload${index}" class="hidden" style="margin-top: 12px;">
        <button class="btn" style="padding: 8px 16px; font-size: 14px; min-width: auto;">Download</button>
      </div>
    `;
    
    fileStatusList.appendChild(fileStatus);
  });
  
  multiFileStatus.appendChild(fileStatusList);
  
  // Hide individual download button, show convert more button
  byId('processingDownload').classList.add('hidden');
  const cmBtn = byId('convertMore');
  if (cmBtn) {
    cmBtn.classList.remove('hidden');
    cmBtn.onclick = () => { window.open('/', '_blank'); };
  }
}

function initializeSingleFileProcessing(file) {
  // Show the original progress bar but add filename display
  byId('progressWrap').classList.remove('hidden');
  
  // Add filename display above progress bar
  const processing = byId('screenProcessing');
  let filenameDisplay = byId('singleFileDisplay');
  if (!filenameDisplay) {
    filenameDisplay = document.createElement('div');
    filenameDisplay.id = 'singleFileDisplay';
    filenameDisplay.style.cssText = 'text-align: center; margin-bottom: 16px;';
    
    const progressWrap = byId('progressWrap');
    processing.insertBefore(filenameDisplay, progressWrap);
  }
  
  filenameDisplay.innerHTML = `
    <h3 style="margin: 0 0 8px 0; color: var(--text); font-size: 16px;">Processing File</h3>
    <p style="margin: 0; color: var(--muted); font-size: 14px; word-break: break-all;">${file.name}</p>
  `;
  
  // Hide multi-file status if it exists
  const multiFileStatus = byId('multiFileStatus');
  if (multiFileStatus) {
    multiFileStatus.style.display = 'none';
  }
  
  // Show the original download button
  byId('processingDownload').classList.remove('hidden');
}

function updateFileStatus(fileIndex, status, message) {
  const upload = window.__activeUploads[fileIndex];
  upload.status = status;
  
  const statusEl = byId(`fileStatusText${fileIndex}`);
  if (statusEl) {
    statusEl.textContent = message || status;
    
    // Update color based on status
    if (status === 'failed') {
      statusEl.style.color = 'var(--error)';
    } else if (status === 'completed') {
      statusEl.style.color = 'var(--success)';
    } else {
      statusEl.style.color = 'var(--muted)';
    }
  }
}

function updateFileProgress(fileIndex, progress) {
  const progressEl = byId(`fileProgress${fileIndex}`);
  if (progressEl) {
    progressEl.style.width = progress + '%';
  }
}

function showFileDownload(fileIndex, downloadUrl, filename) {
  const downloadEl = byId(`fileDownload${fileIndex}`);
  if (downloadEl) {
    downloadEl.classList.remove('hidden');
    const btn = downloadEl.querySelector('button');
    btn.onclick = () => { window.location.href = downloadUrl; };
  }
  
  updateFileProgress(fileIndex, 100);
  updateFileStatus(fileIndex, 'completed', 'Ready for download');
}

async function pollAllFiles() {
  const maxMs = 15 * 60 * 1000; // 15 minutes total
  const intervalMs = 3000; // 3 seconds
  const pollStart = Date.now();
  
  while (Date.now() - pollStart < maxMs) {
    let allCompleted = true;
    
    for (let i = 0; i < window.__activeUploads.length; i++) {
      const upload = window.__activeUploads[i];
      
      if (upload.status === 'processing' || upload.status === 'uploading') {
        allCompleted = false;
        
        if (upload.key && upload.status === 'processing') {
          try {
            const status = await checkStatus(upload.key);
            
            if (status.failed) {
              updateFileStatus(i, 'failed', status.error || 'Conversion failed');
              
              // For single file, update main UI
              if (window.__selectedFiles.length === 1) {
                byId('progressFill').classList.remove('animated');
                byId('percent').classList.remove('hidden');
                setStatus(status.error || 'Conversion failed', 'error');
                byId('convert').disabled = false;
                showScreen('start');
                return;
              }
            } else if (status.ready) {
              const filename = getDownloadFilename(status);
              upload.downloadUrl = status.url;
              showFileDownload(i, status.url, filename);
              
              // For single file, update main download button
              if (window.__selectedFiles.length === 1) {
                byId('progressFill').classList.remove('animated');
                byId('percent').classList.remove('hidden');
                setStatus('Done', 'success');
                setProgress(100);
                const dlBtn = byId('processingDownload');
                dlBtn.disabled = false;
                dlBtn.onclick = () => { window.location.href = status.url; };
                dlBtn.textContent = 'Download';
                const cmBtn = byId('convertMore');
                if (cmBtn) {
                  cmBtn.classList.remove('hidden');
                  cmBtn.onclick = () => { window.open('/', '_blank'); };
                }
              }
            }
          } catch (error) {
            console.error(`Failed to check status for file ${i}:`, error);
          }
        }
      }
    }
    
    if (allCompleted) {
      break;
    }
    
    await new Promise(r => setTimeout(r, intervalMs));
  }
  
  // Check for any files that timed out
  window.__activeUploads.forEach((upload, i) => {
    if (upload.status === 'processing') {
      updateFileStatus(i, 'failed', 'Timed out waiting for conversion');
    }
  });
}

// Wiring
const dropzone = byId('dropzone');
const fileInput = byId('file');

dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.classList.add('drag'); });
dropzone.addEventListener('dragleave', () => dropzone.classList.remove('drag'));
dropzone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropzone.classList.remove('drag');
  const files = e.dataTransfer && e.dataTransfer.files;
  if (files && files.length > 0) {
    addFiles(files);
  }
});

fileInput.addEventListener('change', () => {
  const files = fileInput.files;
  if (files && files.length > 0) {
    addFiles(files);
  }
});

byId('convert').addEventListener('click', () => {
  uploadAndProcess().catch(err => {
    setStatus(err && err.message ? err.message : String(err), 'error');
    byId('convert').disabled = false;
    showScreen('start');
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

def _write_status(upload_key: str, state: str, extra: dict | None = None):
	table = dynamodb.Table(DYNAMO_TABLE)
	payload = {
		"upload_key": upload_key,
		"state": state,
		"source": upload_key,
		"updated_at": int(time.time()),
		"ttl": int(time.time()) + (7 * 24 * 60 * 60)  # 7 days TTL
	}
	if extra:
		payload.update(extra)
	table.put_item(Item=payload)

###############################################################################

def _get_status(upload_key: str) -> dict | None:
	table = dynamodb.Table(DYNAMO_TABLE)
	try:
		response = table.get_item(Key={"upload_key": upload_key})
		return response.get("Item")
	except Exception:
		return None

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
	# Create upload key preserving filename in a unique directory
	uid = uuid.uuid4()
	key = f"uploads/{uid}/{filename}"
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

	# Get status from DynamoDB
	status_payload = _get_status(key)
	if not status_payload:
		return _response(200, {"ready": False})

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
				# If for some reason the output isn't there, return error
				return _response(200, {"ready": False, "failed": True, "error": "Output file not found"})

	# Unknown state
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

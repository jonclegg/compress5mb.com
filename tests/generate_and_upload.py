import os
import json
import time
import pathlib
import random
import string
import subprocess
import mimetypes
from dataclasses import dataclass


API_BASE = os.environ.get("API_BASE", "https://7hme1ull8j.execute-api.us-east-1.amazonaws.com")
CHUNK_SIZE = 10 * 1024 * 1024
MAX_SIZE_BYTES = 200 * 1024 * 1024


def _rand_name(prefix: str, suffix: str) -> str:
    token = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{token}{suffix}"


def _run(cmd: list[str]):
    return subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _ensure_dir(p: pathlib.Path):
    p.mkdir(parents=True, exist_ok=True)


def _gen_image(path: pathlib.Path, target_mb: int):
    # Generate uncompressed BMP to reach large sizes deterministically
    target_bytes = target_mb * 1024 * 1024
    px = max(64, min(16000, int((target_bytes / 3) ** 0.5)))
    _run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"testsrc=size={px}x{px}:rate=1:duration=1", "-frames:v", "1", str(path)])


def _gen_video(path: pathlib.Path, target_mb: int, duration_s: int = 20):
    # Synthesize color bars video with noise and encode with bitrate targeting desired size
    target_bits = target_mb * 1024 * 1024 * 8
    video_kbps = max(300, int(target_bits / duration_s / 1000))
    _run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"testsrc=size=1920x1080:rate=30:duration={duration_s}",
        "-f", "lavfi", "-i", f"sine=frequency=1000:sample_rate=48000:duration={duration_s}",
        "-shortest",
        "-c:v", "libx264", "-preset", "veryfast", "-profile:v", "baseline", "-level", "3.0",
        "-pix_fmt", "yuv420p",
        "-b:v", f"{video_kbps}k", "-maxrate", f"{video_kbps}k", "-bufsize", f"{max(600, video_kbps*2)}k",
        "-c:a", "aac", "-b:a", "96k",
        str(path)
    ])


def _http_json(method: str, url: str, body: dict | None = None) -> dict:
    args = [
        "curl", "-sS", "-X", method, url,
        "-H", "Content-Type: application/json"
    ]
    if body is not None:
        args += ["-d", json.dumps(body)]
    res = _run(args)
    return json.loads(res.stdout.decode("utf-8"))


def _http_get(url: str) -> bytes:
    res = _run(["curl", "-sS", url])
    return res.stdout


def _http_put(url: str, data_path: pathlib.Path) -> dict:
    # Capture response headers to extract ETag
    res = _run(["curl", "-sS", "-D", "-", "-o", "/dev/null", "-X", "PUT", url, "--upload-file", str(data_path)])
    headers = res.stdout.decode("utf-8").splitlines()
    etag = None
    for line in headers:
        if line.lower().startswith("etag:"):
            etag = line.split(":", 1)[1].strip()
            break
    if not etag:
        raise RuntimeError("Missing ETag in PUT response")
    return {"ok": True, "etag": etag}


def multipart_upload(file_path: pathlib.Path) -> dict:
    mime = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    init = _http_json("POST", f"{API_BASE}/api/multipart/initiate", {"filename": file_path.name, "contentType": mime})
    upload_id = init["uploadId"]
    key = init["key"]

    size = file_path.stat().st_size
    num_parts = (size + CHUNK_SIZE - 1) // CHUNK_SIZE
    parts: list[dict] = []
    with open(file_path, "rb") as f:
        for part_number in range(1, num_parts + 1):
            start = (part_number - 1) * CHUNK_SIZE
            end = min(start + CHUNK_SIZE, size)
            f.seek(start)
            chunk_path = file_path.parent / f".{file_path.name}.part{part_number}"
            with open(chunk_path, "wb") as cp:
                cp.write(f.read(end - start))
            presigned = _http_json("GET", f"{API_BASE}/api/multipart/url?key={key}&uploadId={upload_id}&partNumber={part_number}")
            put_res = _http_put(presigned["url"], chunk_path)
            parts.append({"ETag": put_res["etag"], "PartNumber": part_number})
            chunk_path.unlink(missing_ok=True)

    complete = _http_json("POST", f"{API_BASE}/api/multipart/complete", {
        "key": key,
        "uploadId": upload_id,
        "parts": parts,
    })
    return {"key": key, "result": complete}


def poll_status(key: str, timeout_s: int = 900, interval_s: int = 3) -> dict:
    start = time.time()
    while time.time() - start < timeout_s:
        s = _http_json("GET", f"{API_BASE}/api/status?key={key}")
        if s.get("failed"):
            return {"state": "failure", "detail": s}
        if s.get("ready"):
            return {"state": "completed", "detail": s}
        time.sleep(interval_s)
    return {"state": "timeout", "detail": {}}


@dataclass
class Case:
    kind: str  # image|video
    size_mb: int


def build_plan() -> list[Case]:
    sizes = [1, 5, 10, 25, 50, 100, 150, 200]
    plan: list[Case] = []
    for s in sizes:
        plan.append(Case("image", s))
        plan.append(Case("video", s))
    return plan


def main():
    out_dir = pathlib.Path("/Users/jonathanclegg/dev/5mb/tests/artifacts")
    _ensure_dir(out_dir)
    report = {"apiBase": API_BASE, "results": []}

    for case in build_plan():
        fname = _rand_name(case.kind, ".jpg" if case.kind == "image" else ".mp4")
        fpath = out_dir / fname
        t0 = time.time()
        try:
            if case.kind == "image":
                _gen_image(fpath, case.size_mb)
            else:
                _gen_video(fpath, case.size_mb)
            gen_ms = int((time.time() - t0) * 1000)

            up0 = time.time()
            up = multipart_upload(fpath)
            upload_ms = int((time.time() - up0) * 1000)

            ps0 = time.time()
            status = poll_status(up["key"])
            status_ms = int((time.time() - ps0) * 1000)

            report["results"].append({
                "file": str(fpath),
                "kind": case.kind,
                "targetMB": case.size_mb,
                "sizeBytes": fpath.stat().st_size,
                "generationMs": gen_ms,
                "uploadMs": upload_ms,
                "statusMs": status_ms,
                "finalState": status.get("state"),
                "statusDetail": status.get("detail"),
                "success": status.get("state") == "completed",
            })
        except Exception as e:
            report["results"].append({
                "file": str(fpath),
                "kind": case.kind,
                "targetMB": case.size_mb,
                "error": str(e),
                "success": False,
            })

    report_path = out_dir / "report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(str(report_path))


if __name__ == "__main__":
    main()



import os
import json
import tempfile
import subprocess
import logging
import shutil
from decimal import Decimal
import uuid
import imghdr

import boto3

# Note: ImageMagick binaries are available in the layer but ffmpeg is used for compatibility

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

BUCKET_NAME = os.environ["BUCKET_NAME"]
s3 = boto3.client("s3")

TARGET_BYTES = 5 * 1024 * 1024


def _response(status_code, body):
	return {"statusCode": status_code, "body": json.dumps(body)}

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

def _head_object(key: str):
	return s3.head_object(Bucket=BUCKET_NAME, Key=key)

###############################################################################

def _download_to_temp(key: str) -> str:
	# Extract extension from key to preserve it in temp file
	_, _, filename = key.rpartition("/")
	_, _, ext = filename.rpartition(".")
	suffix = f".{ext}" if ext else ""
	
	fd, path = tempfile.mkstemp(suffix=suffix)
	os.close(fd)
	s3.download_file(Bucket=BUCKET_NAME, Key=key, Filename=path)
	return path

###############################################################################

def _upload_from_path(src_path: str, key: str, content_type: str | None = None):
	extra = {"ContentType": content_type} if content_type else {}
	s3.upload_file(Filename=src_path, Bucket=BUCKET_NAME, Key=key, ExtraArgs=extra)

###############################################################################

def _is_video(content_type: str) -> bool:
	return content_type.startswith("video/")


def _is_image(content_type: str) -> bool:
	return content_type.startswith("image/")

###############################################################################

def _detect_image_robust(file_path: str) -> bool:
	"""
	Image detection with fallback to file extensions for formats imghdr misses.
	"""
	# First try imghdr for common formats
	if imghdr.what(file_path) is not None:
		return True
	
	# Fallback: check file extension for formats imghdr doesn't support
	image_extensions = {
		'.heic', '.heif', '.avif', '.webp', '.jxl', '.bpg', 
		'.tiff', '.tif', '.ico', '.psd', '.raw', '.cr2', '.nef', '.arw'
	}
	
	file_ext = os.path.splitext(file_path)[1].lower()
	if file_ext in image_extensions:
		logger.info(f"Detected image by extension: {file_ext}")
		return True
	
	return False

###############################################################################

def _run(cmd: list[str]):
	# no try/except per user preference; fail fast on nonzero
	logger.info(f"Running command: {' '.join(cmd)}")
	result = subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	if result.stderr:
		logger.info(f"Command stderr: {result.stderr.decode()}")
	if result.stdout:
		logger.info(f"Command stdout: {result.stdout.decode()}")
	if result.returncode != 0:
		logger.error(f"Command failed with exit code {result.returncode}")
		logger.error(f"Command stderr: {result.stderr.decode()}")
		raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
	return result

###############################################################################

def _ffmpeg_exists() -> bool:
	return subprocess.call(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0

###############################################################################

def _estimate_video_bitrate(bytes_target: int, duration_seconds: float, audio_kbps: int = 64) -> int:
	if duration_seconds <= 0:
		return 800
	total_kbits = (bytes_target * 8) / 1000
	video_kbps = max(100, int(total_kbits / duration_seconds - audio_kbps))
	return video_kbps

###############################################################################

def _probe_duration(path: str) -> float:
	res = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
	try:
		return float(res.stdout.decode().strip())
	except Exception:
		return 0.0

###############################################################################

def _convert_image(src: str, dst: str):
	# Re-encode as JPEG with decreasing quality until under target
	logger.info(f"Converting image: {src} -> {dst}")
	quality = 85
	while quality >= 40:
		logger.info(f"Trying image quality {quality}")
		_run(["ffmpeg", "-y", "-i", src, "-vf", "scale='min(1920,iw)':-2", "-qscale:v", str(int((100 - quality) / 2) or 1), dst])
		size = os.path.getsize(dst)
		logger.info(f"Image output size: {size} bytes (target: {TARGET_BYTES})")
		if size <= TARGET_BYTES:
			return
		quality -= 10
	# As a fallback, resize more aggressively
	logger.info("Fallback: resizing more aggressively")
	_run(["ffmpeg", "-y", "-i", src, "-vf", "scale='min(1280,iw)':-2", "-qscale:v", "8", dst])
	final_size = os.path.getsize(dst)
	logger.info(f"Final image size: {final_size} bytes")

###############################################################################

def _convert_video(src: str, dst: str):
	logger.info(f"Converting video: {src} -> {dst}")
	duration = _probe_duration(src)
	logger.info(f"Video duration: {duration} seconds")
	video_kbps = _estimate_video_bitrate(TARGET_BYTES, duration)
	logger.info(f"Target video bitrate: {video_kbps} kbps")
	
	# H.264 baseline with constrained bitrate and audio
	_run(["ffmpeg", "-y", "-i", src, "-c:v", "libx264", "-b:v", f"{video_kbps}k", "-maxrate", f"{video_kbps}k", "-bufsize", f"{video_kbps*2}k", "-preset", "veryfast", "-profile:v", "baseline", "-level", "3.0", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "64k", dst])
	
	size = os.path.getsize(dst)
	logger.info(f"Video output size: {size} bytes (target: {TARGET_BYTES})")
	
	# If still too big, scale down and try again
	if size > TARGET_BYTES:
		reduced_kbps = max(300, int(video_kbps*0.75))
		logger.info(f"Video too large, retrying with reduced bitrate: {reduced_kbps} kbps and scaling")
		_run(["ffmpeg", "-y", "-i", src, "-vf", "scale='min(1280,iw)':-2", "-c:v", "libx264", "-b:v", f"{reduced_kbps}k", "-maxrate", f"{reduced_kbps}k", "-bufsize", f"{max(600, int(video_kbps*1.5))}k", "-c:a", "aac", "-b:a", "64k", dst])
		final_size = os.path.getsize(dst)
		logger.info(f"Final video size: {final_size} bytes")

###############################################################################

def handle(event, context):
	logger.info(f"Converter invoked with event: {json.dumps(event)}")
	
	# Log available disk space
	total, used, free = shutil.disk_usage("/tmp")
	logger.info(f"Ephemeral storage: {free // (1024*1024)} MB free, {total // (1024*1024)} MB total")
	
	# S3 put event
	records = event.get("Records") or []
	if not records:
		logger.error("No records in event")
		return _response(400, {"error": "No records"})

	rec = records[0]
	bucket = rec["s3"]["bucket"]["name"]
	key = rec["s3"]["object"]["key"]
	logger.info(f"Processing S3 object: bucket={bucket}, key={key}")
	
	if bucket != BUCKET_NAME:
		logger.warning(f"Bucket mismatch: expected {BUCKET_NAME}, got {bucket}")
		return _response(200, {"skipped": True, "reason": "bucket mismatch"})

	try:
		# Use event size (avoids HeadObject which may be forbidden by bucket policy)
		obj_info = rec.get("s3", {}).get("object", {})
		size = int(obj_info.get("size") or 0)
		logger.info(f"Object size from event: {size} bytes")

		# Mark processing started
		_write_status(key, "processing", {"message": "conversion started"})

		# Log file size but always process
		if size and size <= TARGET_BYTES:
			logger.info(f"File size {size} <= {TARGET_BYTES} bytes, but processing anyway for potential format conversion")

		# Download
		logger.info(f"Downloading {key} to temporary file")
		src_path = _download_to_temp(key)
		logger.info(f"Downloaded to {src_path}")
		
		# Extract filename from uploads/{uid}/{filename} structure
		_, _, filename = key.rpartition("/")
		name_no_ext, _, ext = filename.rpartition(".")
		logger.info(f"Processing file: {filename} (name: {name_no_ext}, ext: {ext})")

		# Decide media type from file contents using robust detection
		media_is_image = _detect_image_robust(src_path)
		logger.info(f"Image detection result for {filename}: {media_is_image}")
		if media_is_image:
			out_key = f"processed/{name_no_ext}.jpg"
			logger.info(f"Converting image to {out_key}")
			with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
				dst_path = tmp.name
			logger.info(f"Image conversion temp file: {dst_path}")
			_convert_image(src_path, dst_path)
			output_size = os.path.getsize(dst_path)
			logger.info(f"Image conversion complete, uploading to {out_key}")
			_upload_from_path(dst_path, out_key, content_type="image/jpeg")
			output_type = "image/jpeg"
			os.unlink(dst_path)
		else:
			out_key = f"processed/{name_no_ext}.mp4"
			logger.info(f"Converting video to {out_key}")
			with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
				dst_path = tmp.name
			logger.info(f"Video conversion temp file: {dst_path}")
			_convert_video(src_path, dst_path)
			output_size = os.path.getsize(dst_path)
			logger.info(f"Video conversion complete, uploading to {out_key}")
			_upload_from_path(dst_path, out_key, content_type="video/mp4")
			output_type = "video/mp4"
			os.unlink(dst_path)

		os.unlink(src_path)
		logger.info(f"Cleaned up source temp file: {src_path}")

		# Generate presigned URL for output to avoid HeadObject during status polling
		url = s3.generate_presigned_url(
			ClientMethod="get_object",
			Params={"Bucket": BUCKET_NAME, "Key": out_key},
			ExpiresIn=3600,
		)
		result = {
			"source": key,
			"output": out_key,
			"outputSize": output_size,
			"outputType": output_type,
			"url": url,
		}
		logger.info(f"Conversion successful: {json.dumps(result)}")
		_write_status(key, "completed", result)
		return _response(200, result)
		
	except Exception as e:
		logger.error(f"Error processing {key}: {str(e)}", exc_info=True)
		try:
			_write_status(key, "failure", {"error": str(e)})
		except Exception:
			pass
		raise

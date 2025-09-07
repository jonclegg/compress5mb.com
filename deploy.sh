
#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   STAGE=dev REGION=us-east-1 AWS_PROFILE=default ./deploy.sh
# Defaults:
: "${STAGE:=dev}"
: "${REGION:=us-east-1}"
: "${AWS_PROFILE:=}"
: "${FFMPEG_VERSION:=release}"
: "${ARCH:=x86_64}"

# Run from repo root
cd "$(dirname "$0")"

# Require Serverless Framework CLI
if ! command -v sls >/dev/null 2>&1; then
	echo "Serverless CLI not found. Install with: npm i -g serverless" >&2
	exit 1
fi

LAYER_DIR="layer"
BIN_DIR="${LAYER_DIR}/bin"
mkdir -p "${BIN_DIR}"

# Build/download ffmpeg layer binaries (linux static)
build_ffmpeg_layer() {
	if [ -x "${BIN_DIR}/ffmpeg" ] && [ -x "${BIN_DIR}/ffprobe" ]; then
		echo "ffmpeg layer already present in ${BIN_DIR}" >&2
		return 0
	fi

	case "${ARCH}" in
		x86_64) DL_ARCH="amd64" ;;
		arm64)  DL_ARCH="arm64" ;;
		*) echo "Unsupported ARCH=${ARCH}. Use x86_64 or arm64." >&2; exit 1 ;;
	esac

	TARBALL_URL="https://johnvansickle.com/ffmpeg/releases/ffmpeg-${FFMPEG_VERSION}-${DL_ARCH}-static.tar.xz"
	TMPDIR="$(mktemp -d)"
	TARBALL="${TMPDIR}/ffmpeg.tar.xz"
	echo "Downloading ${TARBALL_URL}" >&2
	curl -L --fail --silent --show-error -o "${TARBALL}" "${TARBALL_URL}"
	echo "Extracting..." >&2
	tar -xJf "${TARBALL}" -C "${TMPDIR}"
	EXTRACTED_DIR="$(find "${TMPDIR}" -maxdepth 1 -type d -name 'ffmpeg-*static' | head -n 1)"
	if [ ! -d "${EXTRACTED_DIR}" ]; then
		echo "Failed to find extracted ffmpeg directory" >&2
		exit 1
	fi
	cp -f "${EXTRACTED_DIR}/ffmpeg" "${EXTRACTED_DIR}/ffprobe" "${BIN_DIR}/"
	chmod +x "${BIN_DIR}/ffmpeg" "${BIN_DIR}/ffprobe"
	rm -rf "${TMPDIR}"
	echo "ffmpeg and ffprobe installed to ${BIN_DIR}" >&2
}

build_ffmpeg_layer

# Deploy
DEPLOY_CMD=(sls deploy --stage "$STAGE" --region "$REGION" --verbose)
if [ -n "$AWS_PROFILE" ]; then
	DEPLOY_CMD+=(--aws-profile "$AWS_PROFILE")
fi
"${DEPLOY_CMD[@]}"

# Show stack info (no pagination)
INFO_CMD=(sls info --stage "$STAGE" --region "$REGION")
if [ -n "$AWS_PROFILE" ]; then
	INFO_CMD+=(--aws-profile "$AWS_PROFILE")
fi
"${INFO_CMD[@]}" | cat

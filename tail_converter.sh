#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   STAGE=dev REGION=us-east-1 AWS_PROFILE=default ./tail_converter.sh [streamPrefix] [since]
# Examples:
#   ./tail_converter.sh                  # all streams, default since (cw default)
#   ./tail_converter.sh 2025/09/07       # specific stream prefix
#   ./tail_converter.sh 1h               # tail from last 1 hour
#   ./tail_converter.sh 2025/09/07 2d    # prefix + last 2 days
# Tails CloudWatch logs for the converter Lambda using the cw CLI.

: "${STAGE:=dev}"
: "${REGION:=us-east-1}"
: "${AWS_PROFILE:=}"

cd "$(dirname "$0")"

if ! command -v cw >/dev/null 2>&1; then
	echo "cw CLI not found. Install from https://github.com/lucagrulla/cw/releases" >&2
	exit 1
fi

# Derive service name from serverless.yml
SERVICE="$(awk '/^service:/ {print $2; exit}' serverless.yml)"
if [ -z "${SERVICE:-}" ]; then
	echo "Unable to determine service name from serverless.yml" >&2
	exit 1
fi

FUNCTION_NAME="${SERVICE}-${STAGE}-converter"
GROUP="/aws/lambda/${FUNCTION_NAME}"

# Parse optional args: a stream prefix and/or a duration like 1h, 2d, 45m
TARGET_GROUP="$GROUP"
SINCE=""

arg1="${1-}"
arg2="${2-}"

is_duration() {
	# matches 80m, 4h, 4h30m, 2d, 2d4h, 2d4h30m
	[[ "$1" =~ ^([0-9]+d)?([0-9]+h)?([0-9]+m)?$ && "$1" != "" ]]
}

if [ -n "$arg1" ] && is_duration "$arg1"; then
	SINCE="$arg1"
elif [ -n "$arg1" ]; then
	TARGET_GROUP="${GROUP}:$arg1"
fi

if [ -n "$arg2" ]; then
	if is_duration "$arg2"; then
		SINCE="$arg2"
	else
		echo "Unrecognized duration format: $arg2 (expected NdNhNm e.g. 1h, 2d4h30m)" >&2
		exit 1
	fi
fi

CMD=(cw tail "${TARGET_GROUP}" --region "${REGION}" -f)
if [ -n "$SINCE" ]; then
	CMD+=(-b "$SINCE")
fi
if [ -n "$AWS_PROFILE" ]; then
	CMD+=(--profile "$AWS_PROFILE")
fi

exec "${CMD[@]}"



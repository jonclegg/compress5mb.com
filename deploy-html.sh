#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   STAGE=dev REGION=us-east-1 AWS_PROFILE=default ./deploy-html.sh
# Defaults:
: "${STAGE:=dev}"
: "${REGION:=us-east-1}"
: "${AWS_PROFILE:=}"

# Run from repo root
cd "$(dirname "$0")"

# Require Serverless Framework CLI
if ! command -v sls >/dev/null 2>&1; then
	echo "Serverless CLI not found. Install with: npm i -g serverless" >&2
	exit 1
fi

echo "Deploying HTML lambda function..." >&2

# Deploy only the HTML/app function
DEPLOY_CMD=(sls deploy function --function app --stage "$STAGE" --region "$REGION" --verbose)
if [ -n "$AWS_PROFILE" ]; then
	DEPLOY_CMD+=(--aws-profile "$AWS_PROFILE")
fi
"${DEPLOY_CMD[@]}"

# Show function info (no pagination)
INFO_CMD=(sls info --stage "$STAGE" --region "$REGION")
if [ -n "$AWS_PROFILE" ]; then
	INFO_CMD+=(--aws-profile "$AWS_PROFILE")
fi
"${INFO_CMD[@]}" | cat

echo "HTML lambda deployment complete!" >&2

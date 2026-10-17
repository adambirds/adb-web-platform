#!/bin/sh
set -e

QUEUE_NAME=${CELERY_QUEUE:-general}
CONCURRENCY=${CELERY_CONCURRENCY:-2}
WORKER_NAME="worker_${QUEUE_NAME}@$(hostname)"

# --quiet: no start-up banner, so the output is JSON log lines only.
exec celery -A adbsoftwaresolutions --quiet worker \
	-Q "$QUEUE_NAME" \
	-n "$WORKER_NAME" \
	-c "$CONCURRENCY" \
	-l INFO

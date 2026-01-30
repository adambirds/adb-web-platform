#!/bin/sh
set -e

QUEUE_NAME=${CELERY_QUEUE:-default}
CONCURRENCY=${CELERY_CONCURRENCY:-2}
WORKER_NAME="worker_${QUEUE_NAME}@$(hostname)"

exec celery -A adbsoftwaresolutions worker \
	-Q "$QUEUE_NAME" \
	-n "$WORKER_NAME" \
	-c "$CONCURRENCY" \
	-l INFO

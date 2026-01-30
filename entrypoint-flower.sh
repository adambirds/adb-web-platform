#!/bin/sh
exec celery -A adbsoftwaresolutions \
	--broker="$CELERY_BROKER" \
	flower \
	--loglevel=info \
	--address=0.0.0.0 \
	--port=5555 \
	--broker_use_ssl=true \
	--auth_provider="flower.views.auth.GithubLoginHandler" \
	--auth="$FLOWER_AUTH" \
	--oauth2_key="$FLOWER_OAUTH2_KEY" \
	--oauth2_secret="$FLOWER_OAUTH2_SECRET" \
	--oauth2_redirect_uri="$FLOWER_OAUTH2_REDIRECT_URI"

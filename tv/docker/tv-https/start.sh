#!/bin/sh
set -eu
envsubst '${CECH_TLS_SERVER_NAME} ${CECH_TLS_KONOMI_UPSTREAM} ${CECH_TLS_JELLYFIN_UPSTREAM}' < /app/nginx.conf.template > /tmp/nginx.conf
nginx -t -c /tmp/nginx.conf
nginx -c /tmp/nginx.conf -g 'daemon off;' &
master=$!
watch_certificates() {
    generation=$(readlink /tls/current)
    failures=0
    while kill -0 "$master" 2>/dev/null; do
        sleep 30
        next=$(readlink /tls/current)
        if [ "$next" != "$generation" ]; then
            if nginx -t -c /tmp/nginx.conf && nginx -s reload -c /tmp/nginx.conf; then
                generation=$next
                failures=0
                echo 'TLS certificate generation reloaded'
            else
                failures=$((failures + 1))
                if [ "$failures" -ge 3 ]; then
                    echo 'TLS reload watcher stopped after three failures; existing service retained' >&2
                    return 1
                fi
            fi
        fi
    done
}
watch_certificates &
watcher=$!
trap 'kill -QUIT "$master" 2>/dev/null || true; kill "$watcher" 2>/dev/null || true' TERM INT
status=0
wait "$master" || status=$?
kill "$watcher" 2>/dev/null || true
exit "$status"

#!/usr/bin/env bash
set -euo pipefail

show_help() {
    cat <<'HELP'
既存のテレビ連携用HTTPSゲートウェイの管理（Jellyfin標準HTTPSとは別機能）

使い方:
    ./manage-tv-https.sh <enable|disable|status|logs|check>
    ./manage-tv-https.sh -h
    ./manage-tv-https.sh --help

コマンド:
    enable, on     HTTPS gatewayを起動する（自動再起動あり）
    disable, off   HTTPS gatewayだけを停止する
    status         gatewayの稼働状態を表示
    logs           gatewayログを表示（Ctrl+Cで終了）
    check          設定値とCompose構文を検査
    -h, --help     このヘルプを表示

設定:
    .env.example を既存の .env を上書きせずにコピーして設定する。
    必須: CECH_TLS_CERT_GID, CECH_TLS_SERVER_NAME,
          CECH_TLS_BIND, CECH_JELLYFIN_NETWORK
    TLS証明書はTailscale-certificatesが管理する既存のものを使い、
    /etc/tailscale-certsを読み取り専用でマウントする。
    CECH_JELLYFIN_NETWORK はJellyfinとKonomiTVの両方へ
    接続できる既存のDockerネットワークを指定すること。

注意:
    従来どおりTailscale IPと127.0.0.1で7443/8443を公開する。
    KonomiTVの転送先はkonomitv:7000のまま変更しない。
    既存gatewayとポート競合する場合は先に切り替えを計画すること。
    本スクリプトはJellyfinのHTTPサービスや標準HTTPS（8920）を変更しない。
HELP
}

if [[ $# -ne 1 ]]; then
    show_help
    if [[ $# -eq 0 ]]; then
        exit 0
    fi
    exit 2
fi

case "$1" in
    -h|--help)
        show_help
        exit 0
        ;;
    enable|on|disable|off|status|logs|check)
        ;;
    *)
        printf '不明なコマンド: %s\n\n' "$1" >&2
        show_help >&2
        exit 2
        ;;
esac

if ! command -v docker >/dev/null 2>&1; then
    printf 'Dockerが見つからないのじゃ。\n' >&2
    exit 1
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

if [[ ! -f "$SCRIPT_DIR/.env" ]]; then
    printf '設定ファイル .env がないのじゃ。.env.example を参照してくれ。\n' >&2
    exit 1
fi

compose() {
    CECH_TLS_KONOMI_UPSTREAM="${CECH_TLS_KONOMI_UPSTREAM:-konomitv:7000}" \
    CECH_TLS_JELLYFIN_UPSTREAM="${CECH_TLS_JELLYFIN_UPSTREAM:-jellyfin:8096}" \
    docker compose \
        --project-directory "$SCRIPT_DIR" \
        -p tv-https \
        --env-file "$SCRIPT_DIR/.env" \
        -f "$SCRIPT_DIR/tv/docker-compose.https.yml" \
        "$@"
}

case "$1" in
    enable|on)
        compose config --quiet
        compose up -d tv-https
        ;;
    disable|off)
        compose stop tv-https
        ;;
    status)
        compose ps --all tv-https
        ;;
    logs)
        compose logs --tail=100 -f tv-https
        ;;
    check)
        compose config --quiet
        printf 'HTTPS Composeの設定を検査したのじゃ。\n'
        ;;
esac

#!/usr/bin/env bash
set -euo pipefail

show_help() {
    cat <<'HELP'
Jellyfin テレビ向けWeb修正の管理

使い方:
    ./manage-tv.sh <enable|disable|status|logs>
    ./manage-tv.sh -h
    ./manage-tv.sh --help

コマンド:
    enable, on     既存のTVネットワークを使用してTV向けJellyfinをビルド・適用
    disable, off   通常HTTP版Jellyfinに戻す
    status         Jellyfinコンテナの状態とイメージを確認
    logs           Jellyfinのログを表示（Ctrl+Cで終了）
    -h, --help     このヘルプを表示

注意:
    TV版では監査済み固定バージョンのJellyfin Webを使用する。
    enable/disableはJellyfinコンテナを再作成するため再生が中断する。
    必ず事前にconfig/をバックアップし、互換性を確認すること。
    HTTPSゲートウェイと番組表同期は別の機能として管理する。
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
    enable|on|disable|off|status|logs)
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

https_port_active() {
    # 現在公開している8920の設定は、TV版との切り替え後も維持する。
    docker port jellyfin 8920/tcp >/dev/null 2>&1
}

compose_base() {
    local files=(-f "$SCRIPT_DIR/docker-compose.yml")
    if https_port_active; then
        files+=(-f "$SCRIPT_DIR/docker-compose.https.yml")
    fi
    docker compose --project-directory "$SCRIPT_DIR" "${files[@]}" "$@"
}

compose_tv() {
    local files=(-f "$SCRIPT_DIR/docker-compose.yml" -f "$SCRIPT_DIR/docker-compose.tv.yml")
    if https_port_active; then
        files+=(-f "$SCRIPT_DIR/docker-compose.https.yml")
    fi
    docker compose --project-directory "$SCRIPT_DIR" "${files[@]}" "$@"
}

case "$1" in
    enable|on)
        compose_tv config --quiet
        compose_tv up -d --build jellyfin
        ;;
    disable|off)
        compose_base config --quiet
        compose_base up -d --force-recreate jellyfin
        ;;
    status)
        compose_base ps --all jellyfin
        docker inspect --format '使用イメージ: {{.Config.Image}}' jellyfin
        ;;
    logs)
        compose_base logs --tail=100 -f jellyfin
        ;;
esac

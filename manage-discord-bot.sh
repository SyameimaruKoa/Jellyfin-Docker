#!/usr/bin/env bash
set -euo pipefail

show_help() {
    cat <<'HELP'
Jellyfin Discord音楽ボットの起動・停止・状態確認

使い方:
    ./manage-discord-bot.sh <コマンド>
    ./manage-discord-bot.sh -h
    ./manage-discord-bot.sh --help

コマンド:
    enable, on     ボットを起動し、自動再起動を有効にする
    disable, off   ボットだけを停止する（Jellyfinは停止しない）
    status         ボットの状態を表示する
    logs           ボットのログを表示する（Ctrl+Cで終了）
    -h, --help     このヘルプを表示する

初期設定:
    1. .env.example を .env にコピーする（既存の .env は上書きしない）
    2. .env の JELLYFIN_RENDER_GID、Discord Token、
       Jellyfinボット用ユーザー・パスワードを設定する
    3. ./manage-discord-bot.sh enable を実行する

通常の docker compose up -d ではボットは新規起動されない。
enable後は restart: unless-stopped により再起動時も稼働し、
disable後は明示的にenableするまで停止状態を保つ。
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
    printf 'Dockerが見つからないのじゃ。Docker Composeを用意してくれ。\n' >&2
    exit 1
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

compose() {
    docker compose \
        --project-directory "$SCRIPT_DIR" \
        -f "$SCRIPT_DIR/docker-compose.yml" \
        --profile discord-bot \
        "$@"
}

case "$1" in
    enable|on)
        if [[ ! -f "$SCRIPT_DIR/.env" ]]; then
            printf '.env がないのじゃ。.env.example をコピーして設定してくれ。\n' >&2
            exit 1
        fi
        compose config --quiet
        compose up -d jellyfin-discord-bot
        ;;
    disable|off)
        compose stop jellyfin-discord-bot
        ;;
    status)
        compose ps --all jellyfin-discord-bot
        ;;
    logs)
        compose logs --tail=100 -f jellyfin-discord-bot
        ;;
esac

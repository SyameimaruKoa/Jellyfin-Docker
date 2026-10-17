#!/usr/bin/env bash
set -euo pipefail

show_help() {
    cat <<'HELP'
Jellyfin標準HTTPS（8920）のポート公開を管理します。
HTTP 8096は停止せず、Cloudflare Tunnelの内部転送先も変更しません。
テレビ連携の7443/8443は、manage-tv-https.shで別に管理します。

使い方:
    ./manage-https.sh <コマンド>
    ./manage-https.sh -h
    ./manage-https.sh --help

コマンド:
    enable, on     JellyfinのHTTPSポート8920を追加して再作成
    disable, off   8920のポート公開を外して再作成
    status         Jellyfinのポート公開状態を表示
    logs           Jellyfinのログを表示
    check          Compose設定の構文を検査
    -h, --help     このヘルプを表示

注意:
    ポート公開だけではHTTPSは有効になりません。
    Jellyfinの管理画面 → ネットワークでHTTPSを有効化し、
    PFX形式の証明書とパスワードを設定してください。
    HTTPからHTTPSへのリダイレクトは自動設定しません。
    enable/disableでJellyfinコンテナを再作成するため再生が中断します。
HELP
}

if [[ $# -ne 1 ]]; then
    show_help
    [[ $# -eq 0 ]] && exit 0
    exit 2
fi

case "$1" in
    -h|--help) show_help; exit 0 ;;
    enable|on|disable|off|status|logs|check) ;;
    *) printf '不明なコマンド: %s\n\n' "$1" >&2; show_help >&2; exit 2 ;;
esac

if ! command -v docker >/dev/null 2>&1; then
    printf 'Dockerが見つかりません。\n' >&2
    exit 1
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
COMPOSE_FILES=(-f "$SCRIPT_DIR/docker-compose.yml")

# 既にテレビ向けWeb修正版が適用されている場合は、その設定を必ず保持する。
tv_active() {
    local image
    image="$(docker inspect --format '{{.Config.Image}}' jellyfin 2>/dev/null)" || return 1
    [[ "$image" == "cech-jellyfin-live-buffer:local" ]]
}

# 既に8920を公開しているか調べる（Jellyfin内のHTTPS有効状態とは別）。
https_port_active() {
    docker port jellyfin 8920/tcp >/dev/null 2>&1
}

compose() {
    docker compose --project-directory "$SCRIPT_DIR" "${COMPOSE_FILES[@]}" "$@"
}

case "$1" in
    enable|on)
        if tv_active; then
            COMPOSE_FILES+=(-f "$SCRIPT_DIR/docker-compose.tv.yml")
        fi
        COMPOSE_FILES+=(-f "$SCRIPT_DIR/docker-compose.https.yml")
        compose config --quiet
        compose up -d --no-deps jellyfin
        printf '8920を公開しました。Jellyfin側のHTTPS有効化と証明書設定も確認してください。\n'
        ;;
    disable|off)
        if tv_active; then
            COMPOSE_FILES+=(-f "$SCRIPT_DIR/docker-compose.tv.yml")
        fi
        compose config --quiet
        compose up -d --no-deps --force-recreate jellyfin
        printf '8920の公開を外しました。HTTP 8096は維持しています。\n'
        ;;
    check)
        if tv_active; then
            COMPOSE_FILES+=(-f "$SCRIPT_DIR/docker-compose.tv.yml")
        fi
        COMPOSE_FILES+=(-f "$SCRIPT_DIR/docker-compose.https.yml")
        compose config --quiet
        printf 'Jellyfin標準HTTPSのCompose設定に構文上の問題はありません。\n'
        ;;
    status)
        if docker inspect jellyfin >/dev/null 2>&1; then
            docker port jellyfin || true
            if https_port_active; then
                printf '8920のポート公開: 有効（TLS自体の有効化は別途必要）\n'
            else
                printf '8920のポート公開: 無効\n'
            fi
        else
            printf 'Jellyfinコンテナが存在しません。\n'
        fi
        ;;
    logs)
        compose logs --tail=100 -f jellyfin
        ;;
esac

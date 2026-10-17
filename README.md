# Jellyfin Docker

[Jellyfin](https://jellyfin.org/) をDocker Composeで動かす構成じゃ。標準の `docker-compose.yml` はHTTP版のJellyfinのみ。Discord音楽ボット・TV向け修正・HTTPS gatewayはそれぞれ独立した追加ファイルで選択できるのじゃ。

## 初期設定

`.env` にホスト固有の設定を置く。Composeファイル内のパスや認証情報を直接書き換える必要はないぞ。

```bash
cp -n .env.example .env
getent group render
```

既存の `.env` がある場合は**上書きせず**、`.env.example` にある不足分のキーだけ追加すること。

主な設定値は以下じゃ。

| 項目 | 説明 |
| --- | --- |
| `HOST_HOSTNAME` | Jellyfinコンテナのホスト名 |
| `JELLYFIN_UID` / `JELLYFIN_GID` | Jellyfin実行ユーザー・グループID（既定1000） |
| `JELLYFIN_RENDER_GID` | **必須**。ホスト側 `render` グループID |
| `JELLYFIN_VIDEOS_DIR` | 動画フォルダのホスト側パス |
| `JELLYFIN_MUSIC_DIR` | 音楽フォルダのホスト側パス |
| `JELLYFIN_CD_FLAC_DIR` | CDリッピングのホスト側パス |
| `JELLYFIN_PUBLISHED_SERVER_URL` | オプション。クライアントに通知する公開URL |

`JELLYFIN_RENDER_GID` は次のコマンドで数値を調べられる。

```bash
getent group render | cut -d: -f3
```

表示された数値を `.env` の `JELLYFIN_RENDER_GID=` に設定するのじゃ。環境依存のグループIDをComposeにハードコードしないため、未設定の場合はComposeがエラーを出す。

`.env` には認証情報も格納するので、必要に応じて次の権限を設定する。

```bash
chmod 600 .env
```

従来のCloudflare Tunnel等との接続を維持するため、Jellyfin本体のホストポートは **8096:8096 固定**じゃ。環境変数によるポート番号変更は用意しない。

起動するには以下を実行する。

```bash
docker compose up -d
```

## Discord音楽ボット（任意）

ボットは**初期状態では無効**じゃ。`docker-compose.discord-bot.yml` を明示したときだけ構成へ追加するので、通常の `docker compose up -d` では新しく起動されない。

設定を始める前に、Discord Developer Portal でBot Tokenを取得し、Jellyfin側に音楽ライブラリへアクセスできる専用ユーザーを作る。

`.env` で設定する項目は以下じゃ。

| 項目 | 説明 |
| --- | --- |
| `DISCORD_CLIENT_TOKEN` | Discord Bot Token |
| `JELLYFIN_BOT_USERNAME` | ボット専用Jellyfinユーザー名 |
| `JELLYFIN_BOT_PASSWORD` | ボット専用Jellyfinパスワード |
| `JELLYFIN_BOT_SERVER_ADDRESS` | 通常は `http://jellyfin:8096` のままでよい |
| `JELLYFIN_BOT_IMAGE` | ボットのDockerイメージ（任意） |
| `JELLYFIN_BOT_ALLOW_EVERYONE` | Discordコマンドの既定権限（任意） |
| `JELLYFIN_BOT_DISABLE_UPDATE_NOTIFICATIONS` | 更新通知の無効化（任意） |

同じComposeプロジェクトの内部ネットワークからJellyfinへ接続するため、ボット側に音楽ファイルの追加マウントや公開ポートは不要じゃ。パスワードに `$` などを使う場合は `.env` の値を**単一引用符**で囲み、Composeの意図しない変数展開を避けること。

### ボットの起動・停止

```bash
# 最初の1回だけ
chmod +x manage-discord-bot.sh

# 有効化・起動
./manage-discord-bot.sh enable

# 無効化・停止（Jellyfinは稼働したまま）
./manage-discord-bot.sh disable

# 状態確認
./manage-discord-bot.sh status

# ログ確認
./manage-discord-bot.sh logs

# 全コマンドの説明
./manage-discord-bot.sh --help
```

有効化すると `restart: unless-stopped` によりDocker再起動後もボットが起動する。停止したボットは、再度 `enable` を実行するまで自動的には起動しない。

直接Docker Composeを使う場合は、次のコマンドでも同じ操作ができる。

```bash
docker compose -f docker-compose.yml -f docker-compose.discord-bot.yml up -d jellyfin-discord-bot
docker compose -f docker-compose.yml -f docker-compose.discord-bot.yml stop jellyfin-discord-bot
```

### Discord側のコマンド

ボットがDiscord VCへ参加できるように権限を与えること。主なコマンドは `/play`、`/random`、`/shuffle`、`/playlist`、`/status` じゃ。任意フォルダ内だけの再帰シャッフルではなく、Jellyfinのライブラリや再生キューを対象とするぞ。

## TV向け機能（任意）

**標準起動はHTTP版Jellyfinのみ**じゃ。TV向けの追加機能は手動で有効化する。

| ファイル | 用途 |
| --- | --- |
| `docker-compose.yml` | HTTP版Jellyfin本体 |
| `docker-compose.discord-bot.yml` | Discord音楽ボット（手動起動） |
| `docker-compose.tv.yml` | TV向けの固定版Jellyfin Web修正とTV用ネットワーク |
| `docker-compose.https.yml` | Tailscale証明書を使う独立HTTPS gateway（KonomiTV / Jellyfin） |
| `tv/docker-compose.jellyfin-guide-sync.yml` | 番組表同期（従来通り独立管理） |

TV版はWebアセットを監査済みバージョンに固定している。最新Jellyfinと差がある場合もあるため、`config/` をバックアップし、互換性を確認してから適用すること。TV用外部ネットワークの名称は `.env` の `CECH_MEDIA_NETWORK` で設定する。

```bash
./manage-tv.sh enable
./manage-tv.sh status
./manage-tv.sh disable
./manage-tv.sh --help
```

`enable` / `disable` はJellyfinコンテナを再作成するため視聴・音楽再生が中断する。TV版稼働中に通常の `docker compose up -d` を実行するとTV版の構成が外れてしまう場合がある。TV版のまま更新するときは追加ファイルを指定すること。

詳細: [tv/README.md](tv/README.md)

## HTTPS連携（任意・HTTPとは独立）

この機能はJellyfin本体への上書きではない。**別ComposeプロジェクトのNginx gateway**として、既存のTailscale証明書を読み取り専用で使い、KonomiTV用7443とJellyfin用8443を公開する。

`.env` で設定する必須値は `CECH_TLS_CERT_GID`、`CECH_TLS_SERVER_NAME`、`CECH_TLS_BIND`、`CECH_TLS_KONOMI_UPSTREAM`、`CECH_JELLYFIN_NETWORK`。特に `CECH_JELLYFIN_NETWORK` は両バックエンドにアクセス可能な既存Dockerネットワークを指定する。Jellyfin/KonomiTVの接続先と証明書ディレクトリは `.env` から指定する。ただし、従来の連携先を維持するため、HTTPSのホスト側ポートは **7443/8443 固定**、ループバックのバインドも従来どおり `127.0.0.1` のままじゃ。

```bash
./manage-https.sh check
./manage-https.sh enable
./manage-https.sh status
./manage-https.sh disable
./manage-https.sh --help
```

HTTPSを有効にしてもHTTPポート8096のJellyfin本体は変更されない。既存HTTPS gatewayがある場合は7443/8443の競合に注意してくれ。ネットワークに両バックエンドが接続されていない場合、設定が成功してもHTTP中継は失敗するので、その構成を先に確認するのじゃ。

詳細: [tv/HTTPS.md](tv/HTTPS.md)

## 安全上の注意

`.env` は `.gitignore` に含まれており、認証情報をGitHubへコミットしない構成じゃ。既存の `config/`、`cache/` とTV連携コードは削除しない。固定版JellyfinのTV修正を適用する前に互換性とバックアップを確認すること。

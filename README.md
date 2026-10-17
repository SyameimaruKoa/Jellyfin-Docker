# Jellyfin Docker

[Jellyfin](https://jellyfin.org/) を Docker Compose で動かす構成じゃ。既存の動画・音楽マウントを維持しつつ、[Jellyfin Discord Music Bot](https://github.com/manuel-rw/jellyfin-discord-music-bot) を任意で起動できるようにしておる。

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
| `JELLYFIN_HTTP_PORT` | ホスト側HTTPポート（既定8096） |
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

起動するには以下を実行する。

```bash
docker compose up -d
```

## Discord音楽ボット（任意）

ボットは**初期状態では無効**じゃ。Composeの `discord-bot` プロファイルで独立管理しているため、通常の `docker compose up -d` で新しく起動されることはない。

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
docker compose --profile discord-bot up -d jellyfin-discord-bot
docker compose --profile discord-bot stop jellyfin-discord-bot
```

### Discord側のコマンド

ボットがDiscord VCへ参加できるように権限を与えること。主なコマンドは `/play`、`/random`、`/shuffle`、`/playlist`、`/status` じゃ。任意フォルダ内だけの再帰シャッフルではなく、Jellyfinのライブラリや再生キューを対象とするぞ。

## 安全上の注意

`.env` は `.gitignore` に含まれており、認証情報をGitHubへコミットしない構成じゃ。既存の `config/`、`cache/` とTV連携ディレクトリは変更しない。

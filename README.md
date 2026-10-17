# Jellyfin Docker

個人用のDocker Compose構成。既存のポート・メディアパス・テレビ連携機能を変更せず、機能別にファイルを分けています。環境固有の情報と認証情報のみ `.env` で管理します。

## 構成

| ファイル | 内容 |
| --- | --- |
| `docker-compose.yml` | Jellyfin本体。HTTP `8096:8096` のみ |
| `docker-compose.discord-bot.yml` | 音楽ライブラリのDiscordボット |
| `docker-compose.tv.yml` | 既存のテレビ向けWeb修正とTV用ネットワーク |
| `tv/docker-compose.jellyfin-guide-sync.yml` | 既存の番組表同期 |
| `manage-tv.sh` | テレビ向けWeb修正の切り替え |
| `manage-discord-bot.sh` | Discord音楽ボットの起動・停止 |

Jellyfinは通常のHTTP（8096）で使用します。KonomiTV本体とチューナーは別リポジトリで管理しています。

## 初期設定と通常のHTTP起動

```bash
cp -n .env.example .env
getent group render
chmod 600 .env
docker compose up -d
```

既存の `.env` は上書きしないでください。必要な項目だけ追加します。特に `JELLYFIN_RENDER_GID` にはホストの `render` グループIDを設定してください。

通常の起動ではHTTP `8096:8096` だけを公開します。動画・音楽・CDリッピングの既存マウント先やコンテナ名も変更しません。Cloudflare Tunnelの接続先も従来のHTTP 8096のままです。Jellyfin用の追加TLSゲートウェイは設けません。

## Discord音楽ボット（任意）

Jellyfinに音楽ライブラリを読める専用ユーザーを作成し、`.env` に `DISCORD_CLIENT_TOKEN`、`JELLYFIN_BOT_USERNAME`、`JELLYFIN_BOT_PASSWORD` を設定してください。

内部接続は **`http://jellyfin:8096` のまま** です。ボット用の追加ポート公開は不要です。

```bash
./manage-discord-bot.sh enable
./manage-discord-bot.sh disable
./manage-discord-bot.sh status
./manage-discord-bot.sh logs
./manage-discord-bot.sh --help
```

ボットを起動するときは `--no-deps` を使用し、Jellyfin本体を意図せず再作成しないようにしています。Discordコマンドは `/play`、`/random`、`/shuffle`、`/playlist` などが使えます。

## テレビ向けWeb修正（任意）

```bash
./manage-tv.sh enable
./manage-tv.sh disable
./manage-tv.sh status
./manage-tv.sh logs
./manage-tv.sh --help
```

既存のワンセグ向けWeb修正、主副音声選択、`cech-media` ネットワーク連携を維持します。固定Jellyfin Webアセットを利用するため、適用前に `config/` のバックアップと互換性確認が必要です。切り替え時はJellyfinコンテナが再作成され、再生中の処理に影響する場合があります。

詳しくは [tv/README.md](tv/README.md) を参照してください。

## 安全上の注意

認証情報を含む `.env` はGitHubへコミットしないでください。メディアの `config/`、`cache/` は従来どおりGit管理対象外です。実機での動作確認前に既存環境の設定を変更する場合はバックアップを推奨します。

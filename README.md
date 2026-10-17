# Jellyfin Docker

個人用のDocker Compose構成。既存のポート・メディアパス・テレビ連携機能を変更せず、機能別にファイルを分けています。環境固有の情報と認証情報のみ `.env` で管理します。

## 構成

| ファイル | 内容 |
| --- | --- |
| `docker-compose.yml` | Jellyfin本体。HTTP `8096:8096` のみ |
| `docker-compose.https.yml` | **Jellyfin標準HTTPS `8920:8920`** を任意で追加 |
| `docker-compose.discord-bot.yml` | 音楽ライブラリのDiscordボット |
| `docker-compose.tv.yml` | 既存のテレビ向けWeb修正とTV用ネットワーク |
| `tv/docker-compose.https.yml` | **従来のテレビ連携用HTTPSゲートウェイ**。7443/8443のまま維持 |
| `tv/docker-compose.jellyfin-guide-sync.yml` | 既存の番組表同期 |
| `manage-https.sh` | Jellyfin標準HTTPS（8920）の有効・無効 |
| `manage-tv-https.sh` | テレビ連携用ゲートウェイ（7443/8443）の起動・停止 |
| `manage-tv.sh` | テレビ向けWeb修正の切り替え |
| `manage-discord-bot.sh` | Discord音楽ボットの起動・停止 |

**Jellyfinの標準HTTPSと、テレビ連携用Nginxゲートウェイは別機能です。** KonomiTVは別リポジトリで管理するサービスで、Jellyfinの標準HTTPSとは関係ありません。

## 初期設定と通常のHTTP起動

```bash
cp -n .env.example .env
getent group render
chmod 600 .env
docker compose up -d
```

既存の `.env` は上書きしないでください。必要な項目だけ追加します。特に `JELLYFIN_RENDER_GID` にはホストの `render` グループIDを設定してください。

通常の起動ではHTTP `8096:8096` だけを公開します。動画・音楽・CDリッピングの既存マウント先やコンテナ名も変更しません。**Cloudflare Tunnelからは引き続きHTTP 8096で接続できます。** HTTPSへの強制リダイレクトは設定しません。

## Jellyfin標準HTTPS（任意・8920）

Jellyfin本体のHTTPSは初期状態で無効です。必要なときだけ `docker-compose.https.yml` を重ねて8920を公開します。

```bash
./manage-https.sh check
./manage-https.sh enable
./manage-https.sh status
./manage-https.sh disable
./manage-https.sh --help
```

**ポート公開だけではHTTPSは機能しません。** Jellyfinの管理画面 → **ダッシュボード → ネットワーク** でHTTPSを有効化し、PFX形式の証明書のパスと必要な場合はパスワードを設定してください。自己署名証明書も使用できますが、通常はクライアントで信頼警告が出ます。

例えば、自己署名のPFX証明書を `./config/https/jellyfin.pfx` に配置すれば、コンテナ内のパスは `/config/https/jellyfin.pfx` です（`config/` は元のComposeからマウント済み）。

OpenSSLで新しい自己署名証明書を作る場合の一例（名前は実際に接続するFQDNに置き換えてください）:

```bash
mkdir -p config/https
umask 077
openssl req -x509 -newkey rsa:3072 -sha256 -nodes -days 365 \
  -keyout config/https/jellyfin.key \
  -out config/https/jellyfin.crt \
  -subj "/CN=jellyfin.example.local" \
  -addext "subjectAltName=DNS:jellyfin.example.local"
openssl pkcs12 -export \
  -inkey config/https/jellyfin.key \
  -in config/https/jellyfin.crt \
  -out config/https/jellyfin.pfx
# PFXのエクスポートパスワードを対話入力する
# 必要な情報を確認したうえで、一時的な秘密鍵・証明書を削除
rm config/https/jellyfin.key config/https/jellyfin.crt
```

`config/https/jellyfin.pfx` をJellyfinのコンテナユーザー（UID 1000）が読めるようにしてください。PFXパスワードはGitHubへ登録せず、Jellyfinの管理画面で設定します。自己署名証明書は信頼済み認証局の証明書ではないため、公開用途には推奨されません。

`enable` / `disable` はJellyfinコンテナを再作成する場合があるため、再生が中断する可能性があります。テレビ用のWeb修正が稼働している場合は、そのCompose設定を保持するよう管理スクリプト側で判別します。

## Discord音楽ボット（任意）

Jellyfinに音楽ライブラリを読める専用ユーザーを作成し、`.env` に `DISCORD_CLIENT_TOKEN`、`JELLYFIN_BOT_USERNAME`、`JELLYFIN_BOT_PASSWORD` を設定してください。

内部接続は **`http://jellyfin:8096` のまま** です。ボットにHTTPSや追加のポート公開は不要です。

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

既存のワンセグ向けWeb修正、主副音声選択、`cech-media` ネットワーク連携を維持します。固定Jellyfin Webアセットを利用するため、適用前に `config/` のバックアップと互換性確認が必要です。切り替え時はJellyfinコンテナが再作成され、再生中の処理に影響する場合があります。8920が既に公開されている場合はその公開設定も保持する構成です。

詳しくは [tv/README.md](tv/README.md) を参照してください。

## テレビ連携用HTTPSゲートウェイ（任意・従来機能）

このゲートウェイは**Jellyfin本体の8920とは別**です。元から存在する `tv/docker-compose.https.yml`、Nginx設定、Tailscale証明書の更新監視は変更しません。

- KonomiTV用HTTPS: `7443` → `konomitv:7000`（別リポジトリ）
- Jellyfin用HTTPS: `8443` → `jellyfin:8096`
- 証明書: `/etc/tailscale-certs` の既存証明書を読み取り専用でマウント
- これらのゲートウェイはHTTP本体や標準HTTPS 8920から独立

テレビ連携用の操作は次のとおりです。

```bash
./manage-tv-https.sh check
./manage-tv-https.sh enable
./manage-tv-https.sh status
./manage-tv-https.sh disable
./manage-tv-https.sh --help
```

環境固有の `CECH_TLS_CERT_GID`、`CECH_TLS_SERVER_NAME`、`CECH_TLS_BIND`、`CECH_JELLYFIN_NETWORK` は `.env` で指定してください。

**既にゲートウェイが稼働中なら同じ7443/8443を二重公開しないでください。** 旧来のテレビ連携Composeは削除・移行していません。既存のEPG同期やWeb修正プログラムもそのまま残しています。

## 安全上の注意

認証情報を含む `.env`、証明書の秘密鍵やPFXをGitHubへコミットしないでください。メディアの `config/`、`cache/` は従来どおりGit管理対象外です。実機での動作確認前に既存環境の設定を変更する場合はバックアップを推奨します。

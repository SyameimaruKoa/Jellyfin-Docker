# Tailscale HTTPS

既存HTTPアプリの前段に独立Nginxコンテナを追加します。KonomiTVはHTTPS7443、JellyfinはHTTPS8443です。HTTP7000/8096はそのまま利用できます。証明書の取得・更新自体は [Tailscale-certificates](https://github.com/SyameimaruKoa/Tailscale-certificates) に任せ、管理対象の `/etc/tailscale-certs` 親全体を読み取り専用でマウントします。

新しいroot構成では `.env` に設定し、`./manage-https.sh check` で検査してから `./manage-https.sh enable` で独立起動します（停止は `disable`）。HTTP本体やテレビ向けWeb修正に対するCompose上書きは行いません。既存の `tv/docker-compose.https.yml` と `tv/private/https.env` による従来の独立運用も維持します。

以下は従来の `tv/private/https.env` 方式の設定例です。

```
CECH_TLS_CERT_GID=実際のtailscale-certs数値GID
CECH_TLS_SERVER_NAME=証明書のTailscale完全修飾名
CECH_TLS_KONOMI_UPSTREAM=同一ネットワークのKonomiTVコンテナ名:7000
CECH_TLS_JELLYFIN_UPSTREAM=jellyfin:8096
CECH_TLS_BIND=ホストのTailscale IPv4
CECH_JELLYFIN_NETWORK=既存アプリ共通のDockerネットワーク名
```

rootの `.env` 方式でも元の公開ポート（KonomiTV 7443 / Jellyfin 8443）は固定値として維持します。内部の転送先は `konomitv:7000` と `jellyfin:8096`、証明書の配置は `/etc/tailscale-certs` です。`.env` にはPC固有の証明書ホスト名・証明書グループID・Tailscale IPv4・共有Dockerネットワークだけを指定します。`tv/docker-compose.https.yml` の従来構成は変更していません。KonomiTV自体は別リポジトリのサービスです。`CECH_JELLYFIN_NETWORK` は両HTTP転送先へ到達できる既存ネットワークを指定してください。

必要に応じ `CECH_TLS_CERT_DIR` とdigestで固定した `CECH_TLS_IMAGE` を指定できます。起動: `docker compose --project-directory . -p tv-https --env-file tv/private/https.env -f tv/docker-compose.https.yml up -d`。停止:同じComposeで `stop`。既存アプリや証明書サービスの設定変更は不要です。

コンテナはUID1000、証明書グループGID追加、read-only rootfs、capabilitiesなしで動作します。公開ポートは指定Tailscaleアドレスとホストのlocalhostのみ。秘密鍵をコピーせず、ファイル権限も変更しません。

更新時のcurrentリンク変更を30秒ごとに検知し、Nginx構文・証明書検証に成功してからgraceful reloadします。3回失敗すると更新監視だけ停止し、既存のTLSサービスを保持します。原因修正後、同じComposeの `restart tv-https` で監視を再開できます。親ディレクトリのマウントを個別ファイルへ変更しないでください。

WebSocket Upgrade/Connectionを明示して中継し、ライブ配信ではproxy bufferingを無効化します。アップストリームDNSはDocker resolverで再解決します。認証情報を含むURLをaccess logへ保存しません。参考: [Nginx WebSocket](https://nginx.org/en/docs/http/websocket.html)、[Nginx HTTPS](https://nginx.org/en/docs/http/configuring_https_servers.html)。

実機検証では両HTTPS画面・情報API・通常証明書検証・ブラウザーsecure context・Jellyfin認証済WebSocket101を確認。別コンテナの仮証明書を使った世代切替と自動reloadも検証。本番証明書やチューナーへの変更なし。新HTTPS originでは既存アプリの通常ログインが別途必要な場合があります。

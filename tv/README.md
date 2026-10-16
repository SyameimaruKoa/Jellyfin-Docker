# テレビ接続（任意）

USB・mirakc・EPG収集は別リポジトリmirakc-Dockerで管理します。
このディレクトリにはJellyfin側のWeb修正、番組表同期、HTTPS gatewayを置きます。
元のdocker-compose.ymlと既存ライブラリ設定は変更していません。

Composeの相対パスを統一するため、リポジトリrootで元のComposeを先に指定します。
例: `docker compose -f docker-compose.yml -f tv/docker-compose.network.yml -f tv/docker-compose.jellyfin-live-buffer.yml config --quiet`
元のHOST_HOSTNAME/render group等は既存運用の値を設定してください。
Web修正は監査済み固定Jellyfinイメージ用です。別versionへ自動適用しません。
修正用Pythonと番組表同期は標準Pythonのみで、チューナーイメージのbuildを必要としません。

テレビ入力は`http://cech-tv-guide:40774/channels.m3u`、番組表は
`http://cech-tv-guide:40774/guide.xml`です。実際の既存provider設定・ファイル名を確認して利用してください。
視聴URLはM3Uが`http://cech-mirakc:40772`へ向けます。
`tv/docker-compose.jellyfin-guide-sync.yml`は既存providerのXML更新を通常APIへ通知します。
必須環境変数とprivate認証ファイルを設定して使います。
単独起動はrootで`docker compose --project-directory . -f tv/docker-compose.jellyfin-guide-sync.yml up -d`です。認証をGitへ追加しません。

HTTPS gatewayは既存Tailscale証明書をro mountし、KonomiTVにも接続する共有入口です。
rootで`docker compose --project-directory . -p tv-https -f tv/docker-compose.https.yml`を指定し、既存gatewayと同じポートを
同時に公開しないでください。現在の稼働gatewayは移行していません。
USB復旧待ちで、これらの分離ファイルへの実環境移行・実再生は未確認です。

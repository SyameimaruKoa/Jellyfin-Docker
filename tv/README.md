# テレビ接続（任意）

USB・mirakc・EPG収集は別リポジトリmirakc-Dockerで管理します。
このディレクトリにはJellyfin側のWeb修正と番組表同期を置きます。
元のdocker-compose.ymlはHTTP版Jellyfinのみを定義します。既存ライブラリ設定は維持します。

通常はrootの `./manage-tv.sh enable` / `disable` で、既存のTV Web修正とTV用ネットワークをまとめて切り替えるのじゃ。rootの `docker-compose.tv.yml` がこの二つを組み合わせる。従来の個別ファイルも互換用に残しておる。

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

USB復旧待ちで、これらの分離ファイルへの実環境移行・実再生は未確認です。

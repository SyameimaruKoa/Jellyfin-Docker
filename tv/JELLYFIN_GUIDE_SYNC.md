# Jellyfin 番組表の同期

共有XMLTVの内容変更を検知し、Jellyfinの既存XMLTVプロバイダーを設定変更せず再保存してキャッシュを更新します。チューナーを選局せず、番組表更新タスクが実行中なら待機します。最短5分間隔、最大3回連続失敗で停止します。番組表データの受信・全局の鮮度保証とは別の機能です。

`docker-compose.jellyfin-guide-sync.yml` は独立Composeです。既存Jellyfinと同じ外部ネットワークを指定します。環境変数: `CECH_JELLYFIN_NETWORK`, `CECH_SYNC_GUIDE_DIR` (current/guide.xmlの親), `CECH_SYNC_STATE_DIR` (UID1000書込可), `CECH_SYNC_CREDENTIALS`。必要に応じて `CECH_SYNC_IMAGE`, `CECH_SYNC_JELLYFIN_URL`, `CECH_SYNC_PROVIDER_URL` を指定します。イメージには `/opt/venv/bin/python` が必要です。

資格情報ファイルは通常APIで番組表更新権限のあるユーザーのJSON `{"Username":"...","Pw":"..."}`。ローカルの非公開ファイルを読み取り専用でマウントし、Gitに追加しないでください。トークンはメモリ内のみ。ログや同期状態には保存しません。

起動例: `docker compose --project-directory . -p jellyfin-guide-sync --env-file tv/private/guide-sync.env -f tv/docker-compose.jellyfin-guide-sync.yml up -d`。
停止: 同じComposeで `stop`。3回失敗後は接続先・資格情報・タスク結果を確認し、privateのstate/sync.jsonのfailuresを0へ戻してから同じComposeで `up -d`。

番組表生成は同一XMLTV/M3U/ロゴを再保存せず、管理下のUUIDスナップショットを最新8件と10分未満の猶予分だけ保持します。未知ディレクトリやリンクは削除対象外です。
検証: `PYTHONPATH=backend python tests/verify_guide_refresh.py` と `PYTHONPATH=backend python tests/verify_jellyfin_guide_sync.py`。

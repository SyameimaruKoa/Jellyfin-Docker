# ワンセグのJellyfin Web互換再生

固定版Jellyfin Webで、IsInfiniteStream=true・幅1～426/高さ1～240のライブHLSを対象とする。
開始時に3区間を待ち、buffer上限30秒で配信末尾への追い付きを抑える。
さらにH264映像と1～2ch AAC音声を持つ対象のmaster.m3u8だけ、映像copy・音声AAC-LC64kbpsを要求する。
放送音声は再圧縮される。PCE定義のHE-AAC等をブラウザーが拒否する場合の互換処理であり、原音保持とは扱わない。
通常解像度・録画・多ch音声・非AACには音声URL変更を適用しない。native5.1対応を証明しない。

Dockerfileは固定Jellyfin digestから公開Webアセットのみ追加/更新する。
入力hashを検査し、chunk map・runtime・indexの参照を新しいURLへ更新する。
サーバー設定、権限、既存データ、チューナー制御は変更しない。

既存Jellyfin Composeにcompose.jellyfin-live-buffer.yamlを重ねる。
CECH_JELLYFIN_PATCH_DIRはこのディレクトリの絶対パス。
CECH_JELLYFIN_PATCH_TOOL_IMAGEは/opt/venv/bin/pythonを持つbackend imageを指定する。

```sh
CECH_JELLYFIN_PATCH_DIR=/path/to/docker/jellyfin-live \
CECH_JELLYFIN_PATCH_TOOL_IMAGE=cech-zd1-backend:local \
docker compose -f /path/to/jellyfin/docker-compose.yml \
  -f /path/to/compose.jellyfin-live-buffer.yaml build jellyfin
```

既に開いている画面は再読み込みが必要。戻すには追加overlayを外してJellyfinだけ再作成する。
本変更はJellyfin Web向けであり、全フロントでの原音ワンセグ対応完了とは扱わない。
検証結果はhandoff/oneseg-fatal-163.mdに記録する。

単一の2ch AAC音声を持つ対象ワンセグでは、既存の音声選択ポップアップに「主音声（左を両耳）」「副音声（右を両耳）」を追加します。元の音声トラックを選ぶと元の左右に戻ります。常設の追加メニューは表示しません。左右の主副対応はユーザーの実聴報告によります。初期状態では音声経路を変更せず、手動選択時だけ左右を混ぜずに選択側を両側へ送ります。録画・通常解像度・mono・多ch・複数音声は追加操作の対象外です。

固定版のvideo OSDアセットも入力hashを検査し、音声メニューの表示・項目・選択のアンカーが一致した場合だけパッチします。runtime参照を新しいchunk hashへ更新します。サーバーに架空の音声ストリーム番号を渡しません。既存音声の選択処理は保持します。

実際のJellyfinアクションシートを使い、検証用L440Hz/R880Hzで主副・元の左右への復帰を測定しました。ミュート・音量の保持も別途測定済みです。native5.1や全ブラウザーでの動作を証明するものではありません。

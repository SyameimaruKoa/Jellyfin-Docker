ARG JELLYFIN_BASE_IMAGE=jellyfin/jellyfin@sha256:fa7542a7a3c2c80ab6242048db6e8509505ab9d30ff62362b2cc295472e22252
ARG PYTHON_TOOL_IMAGE=python:3.14-slim@sha256:a2b82f3c48559aa0a8446d9af49826b6e2b2016f4cd2afabfe6013ec53729170
FROM ${JELLYFIN_BASE_IMAGE} AS jellyfin-base
FROM ${PYTHON_TOOL_IMAGE} AS patcher
COPY --from=jellyfin-base /jellyfin/jellyfin-web/index.html /upstream/index.html
COPY --from=jellyfin-base /jellyfin/jellyfin-web/runtime.bundle.js /upstream/runtime.bundle.js
COPY --from=jellyfin-base /jellyfin/jellyfin-web/htmlVideoPlayer-plugin.75e5631714895cbf4ff3.chunk.js /upstream/htmlVideoPlayer-plugin.75e5631714895cbf4ff3.chunk.js
COPY --from=jellyfin-base /jellyfin/jellyfin-web/playback-video.a58b5b26b48a669891c4.chunk.js /upstream/playback-video.a58b5b26b48a669891c4.chunk.js
COPY patch_candidate.py patch_native_menu.py build_assets.py audio-channels.js /patch/
RUN python3 /patch/build_assets.py --source /upstream --output /generated
FROM jellyfin-base
COPY --from=patcher /generated/ /jellyfin/jellyfin-web/

"""Generate versioned Jellyfin web assets from the audited fixed image."""
import argparse
import hashlib
from pathlib import Path

from patch_candidate import candidate
from patch_native_menu import candidate as native_menu


PLUGIN = 'htmlVideoPlayer-plugin.75e5631714895cbf4ff3.chunk.js'
RUNTIME_SHA256 = '3b2befafbe5f8a14cb67d03bd58d198be69da125dac1eb269781019e07ce20f9'
INDEX_SHA256 = '04dbe3a2c7fe555747ccd9a8850fed0007bac28609e059dd64d66e213cfce8b9'


def generate(source, output):
    source, output = Path(source), Path(output)
    runtime = (source / 'runtime.bundle.js').read_bytes()
    index = (source / 'index.html').read_bytes()
    if hashlib.sha256(runtime).hexdigest() != RUNTIME_SHA256:
        raise ValueError('Runtime chunk map differs from the audited image')
    if hashlib.sha256(index).hexdigest() != INDEX_SHA256:
        raise ValueError('Jellyfin index differs from the audited image')
    plugin = candidate((source / PLUGIN).read_bytes())
    menu_file = 'playback-video.a58b5b26b48a669891c4.chunk.js'
    menu = native_menu((source / menu_file).read_bytes())
    menu_hash = hashlib.sha256(menu).hexdigest()[:20]
    chunk_hash = hashlib.sha256(plugin).hexdigest()[:20]
    old_hash = '75e5631714895cbf4ff3'
    runtime = runtime.decode()
    if runtime.count(old_hash) != 1:
        raise ValueError('Runtime chunk map anchor differs')
    if runtime.count('a58b5b26b48a669891c4') != 1:
        raise ValueError('Video OSD chunk map differs')
    runtime = runtime.replace('a58b5b26b48a669891c4', menu_hash)
    runtime = runtime.replace(old_hash, chunk_hash).encode()
    runtime_name = 'runtime.cech-' + hashlib.sha256(runtime).hexdigest()[:16] + '.bundle.js'
    index = index.decode()
    anchor = 'src="runtime.bundle.js?'
    if index.count(anchor) != 1:
        raise ValueError('Runtime script reference differs')
    audio = Path(__file__).with_name('audio-channels.js').read_bytes()
    audio_name = 'audio-channels.cech-' + hashlib.sha256(audio).hexdigest()[:16] + '.js'
    if index.count('</body>') != 1:
        raise ValueError('Audio selector script anchor differs')
    index = index.replace('</body>', '<script defer src="' + audio_name + '"></script></body>')
    index = index.replace(anchor, 'src="' + runtime_name + '?').encode()
    if b'node_modules.regenerator-runtime.bundle.js?' not in index:
        raise ValueError('Unrelated regenerator runtime reference changed')
    output.mkdir(parents=True, exist_ok=False)
    (output / PLUGIN.replace(old_hash, chunk_hash)).write_bytes(plugin)
    (output / runtime_name).write_bytes(runtime)
    (output / menu_file.replace('a58b5b26b48a669891c4', menu_hash)).write_bytes(menu)
    (output / 'index.html').write_bytes(index)
    (output / audio_name).write_bytes(audio)
    print('Generated versioned plugin, runtime and index; codec/server configuration unchanged')


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    generate(args.source, args.output)


if __name__ == '__main__':
    main()

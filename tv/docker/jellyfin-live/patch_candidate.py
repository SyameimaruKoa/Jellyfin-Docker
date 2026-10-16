"""Generate the audited low-resolution Jellyfin HLS live-buffer patch.

Only the audited fixed web asset is accepted. This generates a review artifact;
it does not modify a container, authentication, stream timestamps or USB.
The selected low-resolution live URL requests audio-only compatibility encoding.
The live browser verification and its limits are recorded in handoff documents.
"""
import argparse
import hashlib
from pathlib import Path


EXPECTED_SHA256 = '91c080727888a9a56446a71fd722eeb0bd7381dc0cfb1d48ef850ef8d8eeda16'
ANCHOR = 'maxBufferLength:u,maxMaxBufferLength:u,'
CONDITION = ('t.mediaSource?.IsInfiniteStream===!0&&'
    't.mediaSource.MediaStreams?.some(v=>v.Type==="Video"&&'
    'v.Width>0&&v.Width<=426&&v.Height>0&&v.Height<=240)')


def candidate(raw):
    if hashlib.sha256(raw).hexdigest() != EXPECTED_SHA256:
        raise ValueError('Jellyfin web asset differs from the audited source')
    source = raw.decode()
    if source.count(ANCHOR) != 1:
        raise ValueError('HLS options anchor differs')
    replacement = (f'initialLiveManifestSize:({CONDITION})?3:1,'
        f'maxBufferLength:({CONDITION})?30:u,'
        f'maxMaxBufferLength:({CONDITION})?30:u,')
    source = source.replace(ANCHOR, replacement)
    url_anchor = 'i=n.url,console.debug'
    if source.count(url_anchor) != 1:
        raise ValueError('Playback URL anchor differs')
    # The MPEG-TS copy path can expose PCE-defined HE-AAC that browsers reject.
    # Limit compatibility audio to small H264 live streams with one/two AAC channels.
    condition = CONDITION.replace('t.mediaSource', 'n.mediaSource')
    condition += ('&&n.mediaSource.MediaStreams.some(v=>v.Type==="Video"&&v.Codec==="h264")'
        '&&n.mediaSource.MediaStreams.some(v=>v.Type==="Audio"&&v.Codec==="aac"'
        '&&v.Channels>0&&v.Channels<=2)')
    selector_condition = (condition + '&&n.mediaSource.MediaStreams.filter(v=>v.Type==="Audio").length===1'
        '&&n.mediaSource.MediaStreams.some(v=>v.Type==="Audio"&&v.Channels===2)')
    audio_url = ('i=n.url,window.dispatchEvent(new CustomEvent("cech-oneseg-audio",{detail:(' + selector_condition + ')})),i=(()=>{if(!(' + condition + '))return i;'
        'const url=new URL(i,window.location.href);'
        'if(!url.pathname.endsWith("/master.m3u8"))return i;'
        'url.searchParams.set("allowAudioStreamCopy","false");'
        'url.searchParams.set("allowVideoStreamCopy","true");'
        'url.searchParams.set("AudioCodec","aac");'
        'url.searchParams.set("aac-profile","lc");'
        'url.searchParams.set("AudioBitrate","64000");'
        'return url.href})(),console.debug')
    return source.replace(url_anchor, audio_url).encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = candidate(args.input.read_bytes())
    with args.output.open('xb') as output:
        output.write(result)
    print('Audited web patch written; no direct deployment performed')


if __name__ == '__main__':
    main()

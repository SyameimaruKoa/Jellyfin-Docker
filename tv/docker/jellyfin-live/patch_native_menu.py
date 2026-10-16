"""Bind manual one-seg channels to the audited existing Jellyfin audio sheet."""
import hashlib

EXPECTED_SHA256 = '7ec60e6688b166010ad9dee68aecb42f639d83abb8aa8e85de5bafd57ccdf7a1'


def candidate(raw):
    if hashlib.sha256(raw).hexdigest() != EXPECTED_SHA256:
        raise ValueError('Jellyfin video OSD differs from the audited source')
    source = raw.decode()
    # A missing EPG entry does not turn a live TV channel into a finite video.
    anchor = 'return!("TvChannel"!==e.Type||!e.CurrentProgram)'
    if source.count(anchor) != 1:
        raise ValueError('Live TV classification anchor differs')
    source = source.replace(anchor, 'return "TvChannel"===e.Type')
    anchor = 'y.f.audioTracks(t).length>1?e.querySelector(".btnAudio").classList.remove("hide")'
    if source.count(anchor) != 1:
        raise ValueError('Audio button visibility anchor differs')
    source = source.replace(anchor, '(y.f.audioTracks(t).length>1||window.cechOneSegAudio?.available())?e.querySelector(".btnAudio").classList.remove("hide")')
    anchor = 'i=t.map((function(e){var t={name:e.DisplayTitle,id:e.Index};return e.Index===n&&(t.selected=!0),t})),a=this;'
    if source.count(anchor) != 1:
        raise ValueError('Audio action sheet items anchor differs')
    replacement = ('i=t.map((function(e){var t={name:e.DisplayTitle,id:e.Index};return e.Index===n&&(t.selected=!0),t})),'
        'i=(()=>{if(!window.cechOneSegAudio?.available())return i;'
        'const mode=window.cechOneSegAudio.mode();if(mode!=="original")for(const item of i)item.selected=!1;'
        'return i.concat([{id:"cech-main",name:"主音声（左を両耳）",selected:mode==="left"},'
        '{id:"cech-sub",name:"副音声（右を両耳）",selected:mode==="right"}])})(),a=this;')
    source = source.replace(anchor, replacement)
    anchor = 'then((function(t){var r=parseInt(t,10);r!==n&&y.f.setAudioStreamIndex(r,e)}))'
    if source.count(anchor) != 1:
        raise ValueError('Audio action sheet selection anchor differs')
    replacement = ('then((async function(t){if(t==="cech-main"||t==="cech-sub"){'
        'await window.cechOneSegAudio.choose(t==="cech-main"?"left":"right");return}'
        'await window.cechOneSegAudio?.choose("original");'
        'var r=parseInt(t,10);r!==n&&y.f.setAudioStreamIndex(r,e)}))')
    return source.replace(anchor, replacement).encode()

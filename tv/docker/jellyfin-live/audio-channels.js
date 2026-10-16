/* Manual one-seg listening, controlled by Jellyfin's existing audio menu. */
(() => {
    'use strict';
    let eligible = false;
    let context;
    let active;
    let mode = 'original';
    let generation = 0;
    const graphs = new WeakMap();
    function video() {
        return [...document.querySelectorAll('video')].find(v => !v.ended && v.videoWidth > 0 && v.videoWidth <= 426 && v.videoHeight > 0 && v.videoHeight <= 240);
    }
    function route(graph, choice) {
        if (graph.mode === choice) return;
        graph.mode = null;
        graph.source.disconnect();
        graph.splitter.disconnect();
        graph.merger.disconnect();
        if (choice === 'original') graph.source.connect(context.destination);
        else {
            graph.source.connect(graph.splitter);
            const channel = choice === 'left' ? 0 : 1;
            graph.splitter.connect(graph.merger, channel, 0);
            graph.splitter.connect(graph.merger, channel, 1);
            graph.merger.connect(context.destination);
        }
        graph.mode = choice;
    }
    function reset() {
        generation++;
        mode = 'original';
        if (active) route(active, 'original');
    }
    const bridge = window.cechOneSegAudio = {
        available: () => eligible && !!video(),
        mode: () => mode,
        async choose(choice) {
            if (!['left', 'right', 'original'].includes(choice)) return false;
            if (choice === 'original' && !bridge.available()) { reset(); return true; }
            if (!bridge.available()) return false;
            const media = video();
            const request = ++generation;
            if (choice === 'original' && !graphs.has(media)) { mode = choice; return true; }
            try {
                context ||= new AudioContext();
                await context.resume();
                if (request !== generation || !bridge.available() || video() !== media) return false;
                let graph = graphs.get(media);
                if (!graph) {
                    const splitter = context.createChannelSplitter(2);
                    const merger = context.createChannelMerger(2);
                    graph = {source: context.createMediaElementSource(media), splitter, merger};
                    graphs.set(media, graph);
                }
                if (active && active !== graph) route(active, 'original');
                active = graph;
                route(graph, choice);
                mode = choice;
                return true;
            } catch (error) {
                if (request === generation) reset();
                throw error;
            }
        }
    };
    function update() {
        if (bridge.available()) for (const button of document.querySelectorAll('.btnAudio')) button.classList.remove('hide');
    }
    window.addEventListener('cech-oneseg-audio', event => {
        reset();
        eligible = event.detail === true;
        update();
    });
    document.addEventListener('loadedmetadata', update, true);
    for (const name of ['emptied', 'ended']) document.addEventListener(name, reset, true);
    new MutationObserver(update).observe(document.body, {childList: true, subtree: true});
})();

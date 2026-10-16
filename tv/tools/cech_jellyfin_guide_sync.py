"""Synchronize published XMLTV changes through Jellyfin's normal API; no tuning."""
import argparse
import hashlib
import json
from pathlib import Path
import signal
import threading
import time
import urllib.request


class Jellyfin:
    def __init__(self, base, credentials):
        self.base = base.rstrip('/')
        self.authorization = 'MediaBrowser Client="CECH guide sync", Device="Guide sync", DeviceId="cech-guide-sync", Version="1.0"'
        login = self.call('/Users/AuthenticateByName', credentials)
        self.authorization += ', Token="' + login['AccessToken'] + '"'

    def call(self, path, body=None):
        data = None if body is None else json.dumps(body).encode()
        request = urllib.request.Request(self.base + path, data=data, headers={
            'Authorization': self.authorization, 'Content-Type': 'application/json'})
        with urllib.request.urlopen(request, timeout=20) as response:
            content = response.read()
            return json.loads(content) if content else None

    def task(self):
        rows = [t for t in self.call('/ScheduledTasks') if t.get('Key') == 'RefreshGuide']
        if len(rows) != 1:
            raise ValueError('Expected one RefreshGuide task')
        return rows[0]


def synchronize(api, expected_url, stopped, *, timeout=120, interval=2):
    task = api.task()
    if task['State'] != 'Idle':
        return False
    # Preserve all existing mappings and options; invalidate only this provider cache.
    config = api.call('/System/Configuration/livetv')
    providers = [p for p in config['ListingProviders'] if p.get('Type', '').lower() == 'xmltv' and p.get('Path') == expected_url]
    if len(providers) != 1:
        raise ValueError('Expected exactly one matching XMLTV provider')
    previous = (task.get('LastExecutionResult') or {}).get('EndTimeUtc')
    api.call('/LiveTv/ListingProviders?validateListings=true&validateLogin=false', providers[0])
    deadline = time.monotonic() + timeout
    while not stopped.is_set() and time.monotonic() < deadline:
        latest = api.task()
        result = latest.get('LastExecutionResult') or {}
        if latest['State'] == 'Idle' and result.get('EndTimeUtc') != previous:
            if result.get('Status') != 'Completed':
                raise ValueError('Guide refresh did not complete successfully')
            return True
        stopped.wait(interval)
    raise TimeoutError('Guide refresh completion was not observed')


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--base-url', required=True)
    parser.add_argument('--provider-url', required=True)
    parser.add_argument('--guide', type=Path, required=True)
    parser.add_argument('--credentials', type=Path, required=True)
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--interval', type=int, default=60)
    parser.add_argument('--minimum-refresh-interval', type=int, default=300)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    if args.interval < 30 or args.minimum_refresh_interval < 60:
        parser.error('Intervals must be at least 30 and 60 seconds respectively')
    stopped = threading.Event()
    for number in (signal.SIGINT, signal.SIGTERM):
        signal.signal(number, lambda *_: stopped.set())
    state = json.loads(args.state.read_text()) if args.state.exists() else {}
    while not stopped.is_set():
        if state.get('failures', 0) >= 3:
            print(json.dumps({'paused': True, 'reason': 'three_consecutive_failures', 'hardware_io': False}), flush=True)
            return 1
        try:
            digest = hashlib.sha256(args.guide.read_bytes()).hexdigest()
            due = time.time() - state.get('last_success', 0) >= args.minimum_refresh_interval
            if digest != state.get('digest') and due:
                credentials = json.loads(args.credentials.read_text())
                api = Jellyfin(args.base_url, credentials)
                if synchronize(api, args.provider_url, stopped):
                    state = dict(digest=digest, last_success=time.time(), failures=0)
                    print(json.dumps({'synchronized': True, 'hardware_io': False}), flush=True)
        except (OSError, ValueError, KeyError, TypeError) as error:
            # Never log authentication payloads, tokens, response bodies or URLs.
            state['failures'] = state.get('failures', 0) + 1
            print(json.dumps({'synchronized': False, 'error_type': type(error).__name__, 'failures': state['failures'], 'hardware_io': False}), flush=True)
        args.state.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.state.with_suffix('.tmp')
        temporary.write_text(json.dumps(state, indent=2))
        temporary.replace(args.state)
        if args.once:
            return int(state.get('failures', 0) > 0)
        stopped.wait(args.interval)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

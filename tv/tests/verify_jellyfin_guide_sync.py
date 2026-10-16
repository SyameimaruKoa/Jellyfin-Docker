"""Exercise refresh completion, busy deferral and failures without tuning."""
import threading
from cech_jellyfin_guide_sync import synchronize


class API:
    def __init__(self, busy=False, failure=False):
        self.calls = []
        self.polls = 0
        self.busy = busy
        self.failure = failure
        self.provider = {'Type': 'xmltv', 'Path': 'http://guide/guide.xml', 'Mappings': [{'a': 'b'}]}

    def task(self):
        self.polls += 1
        result = {'EndTimeUtc': 'old', 'Status': 'Completed'}
        state = 'Running' if self.busy else 'Idle'
        # An immediately Idle response is stale, not proof of completion.
        if self.polls >= 3:
            result = {'EndTimeUtc': 'new', 'Status': 'Failed' if self.failure else 'Completed'}
        return {'State': state, 'LastExecutionResult': result}

    def call(self, path, body=None):
        self.calls.append((path, body))
        if path == '/System/Configuration/livetv':
            return {'ListingProviders': [self.provider]}
        assert body == self.provider


def main():
    api = API()
    assert synchronize(api, api.provider['Path'], threading.Event(), interval=0)
    assert api.polls == 3
    assert len(api.calls) == 2
    busy = API(busy=True)
    assert not synchronize(busy, busy.provider['Path'], threading.Event(), interval=0)
    assert not busy.calls
    for api, url in [(API(failure=True), 'http://guide/guide.xml'), (API(), 'http://wrong/guide.xml')]:
        try:
            synchronize(api, url, threading.Event(), interval=0)
        except ValueError:
            pass
        else:
            raise AssertionError('Accepted failed refresh or mismatched provider')
    print('Verified completion, stale Idle, busy deferral, exact provider preservation and failures; hardware_io=False')


if __name__ == '__main__':
    main()

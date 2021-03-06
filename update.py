import json
import threading
from time import sleep
from tarfile import open as tar
from tempfile import TemporaryFile
from binascii import hexlify
from requests import get
from hashlib import sha256
from pathlib import Path


class Error(Exception):
    pass


class JsonHook:
    def __init__(self, name: str, default: dict = None, *, indent=4):
        self._name = name
        self._indent = indent
        self._existed = Path(name).exists()
        if self._existed:
            with open(name) as file:
                self._json = json.load(file)
        else:
            self._json = default or {}
            self.dump()

    def dump(self):
        with open(self._name, 'w') as file:
            json.dump(self._json, file,
                      indent=self._indent,
                      sort_keys=True)

    def __delitem__(self, key):
        del self._json[key]
        self.dump()

    def __getitem__(self, key):
        return self._json[key]

    def __setitem__(self, key, value):
        self._json[key] = value
        self.dump()


v = JsonHook('version.json', {
    'current': '',
    'get-version': 'latest'
})


class Feed:
    def __init__(self, pattern: str, end='\r'):
        self.pattern = pattern
        self.end = end
        self.prev = 0

    def print(self, data):
        n_str = self.pattern % data
        print(n_str + ' '*(self.prev - len(n_str)), end=self.end)
        self.prev = len(n_str)

    def close(self, msg: str):
        print(msg + ' '*(self.prev - len(msg)))


class Counter:
    def __init__(self, n=0):
        self.n = n

    def __str__(self):
        return str(self.n)

    def __add__(self, other):
        self.n += other
        return self

    def __sub__(self, other):
        self.n -= other
        return self


def calculate_hash(force=False, lines: Counter = 0, chars: Counter = 0):
    if v['current'] and not force:
        return v['current']

    py_files = {str(p): p for p in Path().rglob('*.py')}
    sha = sha256()
    display = Feed('Hashing %s')
    for path in sorted(py_files):
        with py_files[path].open('rb') as file:
            display.print(path)
            sleep(wait)
            for line in file:
                lines += 1
                chars += len(line)
                sha.update(line)
    display.close('Finished hash.')
    h = hexlify(sha.digest()).decode('utf-8')
    v['current'] = h
    return h


def grab_version(latest=False):
    if latest:
        url = 'https://raw.githubusercontent.com/Tankobot' \
              '/p2pg/master/version.json'
    else:
        url = 'https://tankobot.github.io' \
              '/p2pg/version.json'
    print('Getting version information...')
    wheel.start()
    result = get(url).json()
    wheel.stop()
    return result


class Wheel:
    def __init__(self):
        self.before = None
        self.speed = None
        self.clockwise = None
        self._state_lock = threading.Lock()
        self._state = False
        self._thread = None

    @property
    def state(self):
        with self._state_lock:
            return self._state

    @state.setter
    def state(self, value):
        with self._state_lock:
            self._state = bool(value)

    def loop(self):
        place = 0
        frames = ('-', '\\', '|', '/')
        direction = 1 if self.clockwise else -1
        while self.state:
            print(self.before + frames[place], end='\r')
            place += direction
            place %= len(frames)
            sleep(1 / self.speed)
        print(' ' * (len(self.before) + 1), end='\r')

    def start(self, before='   ', speed=4, clockwise=True):
        self.state = True
        self.before = before
        self.speed = speed
        self.clockwise = clockwise
        if self._thread:
            raise Error('wheel already started')
        else:
            self._thread = threading.Thread(target=self.loop)
            self._thread.start()

    def stop(self):
        self.state = False
        # ignore call if no thread exists
        if not self._thread:
            return
        self._thread.join(1)
        if self._thread.is_alive():
            raise Error('wheel did not terminate')
        else:
            self.before = '   '
            self._thread = None


def download_version(version: str = None, v_info=None, chunk_size=128):
    version = version or v['get-version']
    if version == 'latest':
        v_info = v_info or grab_version(True)
        n_sig = v_info['current']
        url = 'https://github.com/Tankobot' \
              '/p2pg/archive/master.tar.gz'
    else:
        v_info = v_info or grab_version()
        n_sig = v_info[version][0]
        url = v_info[version][1]
    if v['current'] != n_sig:
        print('latest: %s' % n_sig)
        print('Downloading version (%s)' % version)
        wheel.start()
        new_version = get(url, stream=True)
        file = TemporaryFile(buffering=0)

        # handle if the file length can't be retrieved
        try:
            total = int(new_version.headers['content-length'])
        except KeyError:
            total = 0

        place = 0
        wheel.stop()
        if not total:
            wheel.start('Downloading... ')

        for chunk in new_version.iter_content(chunk_size):
            file.write(chunk)
            place += len(chunk)
            if total:
                percentage = str(round(place/total * 100, 1)).rjust(5)
                print('Downloading... %s' % percentage, end='\r')

        wheel.stop()
        print('Finished downloading.')
        file.seek(0)
        return file, n_sig


def remove_folder(tar_file):
    tar_info = tar_file.next()
    display = Feed('Extracting %s')
    while tar_info:
        tar_info.name = tar_info.name.partition('/')[2]
        if tar_info.name:
            display.print(tar_info.name)
            sleep(wait)
            yield tar_info
        tar_info = tar_file.next()
    display.close('Finished extraction.')


def install(version: str, v_info=None, chunk_size=None):
    archive, n_sig = download_version(version, v_info, chunk_size)
    print('Installing (%s)...' % version)
    try:
        with tar(mode='r:gz', fileobj=archive) as file:
            file.extractall(members=remove_folder(file))
    finally:
        archive.close()
    print('Verifying installation...')
    _sha = calculate_hash(True)
    print('   sha: %s' % _sha)
    if _sha != n_sig:
        print('##### Install corrupted!')
        print('##### Please try downloading p2pg again.')
    print('Finished installing.')


wait = 0
wheel = Wheel()


def main():
    from argparse import ArgumentParser
    parser = ArgumentParser(description='Update p2pg.')
    parser.add_argument('-j', '--just-hash', dest='just_hash',
                        action='store_true', help='only display/write hash')
    parser.add_argument('-c', '--chunk', dest='chunk_size',
                        metavar='INT',
                        type=int, help='chunk key_size')
    parser.add_argument('-w', '--wait', dest='wait',
                        default=0, type=float,
                        help='seconds to wait between actions')
    args = parser.parse_args()
    global wait
    wait = args.wait

    print('Calculating hash...')
    number_of_lines = Counter()
    number_of_chars = Counter()
    _sha = calculate_hash(True, number_of_lines, number_of_chars)
    print(' lines: %s' % number_of_lines)
    print(' chars: %s' % number_of_chars)
    print('   sha: %s' % _sha)
    if args.just_hash:
        return
    if input('Update y/[n]: ') == 'y':
        v_default = v['get-version']
        wanted = input('Version [%s]: ' % v_default).strip() or v_default
        v_latest = True if wanted == 'latest' else False
        if v_latest:
            info = grab_version(True)
            if v['current'] == info['current']:
                print('Already up to date (%s)' % wanted)
            else:
                install(wanted, info, args.chunk_size)
        else:
            info = grab_version()
            if wanted not in info:
                raise Error('requested version does not exist')
            if v['current'] == info[wanted][0]:
                print('Already up to date (%s)' % wanted)
            else:
                install(wanted, info, args.chunk_size)


if __name__ == '__main__':
    main()

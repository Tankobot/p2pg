import json
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


def calculate_hash(force=False):
    if v['current'] and not force:
        return v['current']

    py_files = {str(p): p for p in Path().rglob('*.py')}
    sha = sha256()
    for path in sorted(py_files):
        with py_files[path].open('rb') as file:
            print('Hashing %s' % path)
            for line in file:
                sha.update(line)
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
    print('Getting version info...')
    return get(url).json()


def download_version(version: str = None, chunk_size=128):
    version = version or v['get-version']
    if version == 'latest':
        v_info = grab_version(True)
        n_sig = v_info['current']
        url = 'https://github.com/Tankobot' \
              '/p2pg/archive/master.tar.gz'
    else:
        v_info = grab_version()
        n_sig = v_info[version][0]
        url = v_info[version][1]
    if v['current'] != n_sig:
        print('Downloading version (%s)' % version)
        new_version = get(url, stream=True)
        file = TemporaryFile(buffering=0)
        total = new_version.headers['content-size']
        place = 0
        for chunk in new_version.iter_content(chunk_size):
            file.write(chunk)
            place += len(chunk)
            percentage = str(round(place / total, 1)).ljust(5)
            print('Downloading... %s' % percentage, end='\r')
        print()
        file.seek(0)
        return file


def install(version: str):
    archive = download_version(version)
    print('Installing (%s)...' % archive)
    try:
        with tar(mode='r:gz', fileobj=archive) as file:
            file.extractall()
    finally:
        archive.close()


if __name__ == '__main__':
    print('Calculating hash...')
    _sha = calculate_hash(True)
    print('   sha: %s' % _sha)
    if input('Update y/[n]: ') == 'y':
        v_default = v['get-version']
        wanted = input('Version [%s]: ' % v_default).strip() or v_default
        v_latest = True if wanted == 'latest' else False
        if v_latest:
            info = grab_version(True)
            if v['current'] == info['current']:
                print('Already up to date (%s)' % wanted)
            else:
                install(wanted)
        else:
            info = grab_version()
            if wanted not in info:
                raise Error('requested version does not exist')
            if v['current'] == info[wanted][0]:
                print('Already up to date (%s)' % wanted)
            else:
                install(wanted)

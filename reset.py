from logging import getLogger, DEBUG, StreamHandler, Formatter
from argparse import ArgumentParser
from pathlib import Path


__author__ = 'Michael Bradley'
__copyright__ = 'GNU General Public License V3'


log = getLogger(__name__)
log.propagate = False
handler = StreamHandler()
handler.setFormatter(Formatter())
log.addHandler(handler)


def attempt_unlink(path, msg: str):
    if Path(path).exists():
        Path(path).unlink()
    else:
        log.warning(msg)


def rem_config():
    log.info('removing config file...')
    attempt_unlink('conf.json', 'config file missing')


def rem_data():
    """Remove all data files under the data directory."""

    log.info('removing data files...')
    for path in Path('data').iterdir():
        if path != Path('data/example.json'):
            log.debug('    removing %s...' % path)
            if path.is_dir():
                path.rmdir()
            else:
                path.unlink()


def rem_log():
    log.info('removing log...')
    attempt_unlink('general.log', 'log file missing')


def main():
    parser = ArgumentParser(description='Resets all p2pg user files.')
    parser.add_argument('subjects', nargs='?', default=None,
                        help='specify region to reset')
    parser.add_argument('-p', '--possible', action='store_true',
                        help='list supported subjects')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='increase verbosity')
    parser.add_argument('-f', '--force', action='store_true',
                        help='ignore confirmation warning')
    args = parser.parse_args()

    if args.verbose:
        log.setLevel(DEBUG)

    if args.possible:
        print('Possible subjects:')
        for subject in globals():
            if subject.startswith('rem_'):
                print('    ' + subject[4:])
        return

    print('Resetting %s...' % (args.subjects or 'all subjects'))

    if args.subjects:
        # evaluate only subjects
        if isinstance(args.subjects, list):
            for func in args.subjects:
                if ('rem_' + func) in globals():
                    globals()['rem_' + func]()
                else:
                    log.error('incorrect subject %s', func)
        else:
            if ('rem_' + args.subjects) in globals():
                globals()['rem_' + args.subjects]()
            else:
                log.error('incorrect subject %s', args.subjects)
    else:
        # confirm reset action
        if not args.force:
            if input('Are you sure y/[n]: ').lower() != 'y':
                return

        # evaluate all subjects
        for func in globals():
            if func.startswith('rem_'):
                globals()[func]()

    print('Finished reset.')


if __name__ == '__main__':
    main()

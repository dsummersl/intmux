import argparse
import logging
import posix
import sys

from . import tmux

logger = logging.getLogger('intmux')


def main():
    parser = argparse.ArgumentParser(
        description="Connect to several hosts in a tmux session."
    )

    parser.add_argument(
        '--log', '-l', default="WARN",
        help="Log level (default: WARN)")
    parser.add_argument(
        '--command', '-c', default="",
        help="Command to execute when connecting to a remote host")
    parser.add_argument(
        '--input', '-i', nargs='?', type=argparse.FileType('r'), default=None,
        help="Read list of hosts from input file when provided, otherwise from STDIN.")
    parser.add_argument(
        '--script', '-s', default="",
        help="Execute commands in local file remotely")

    parser.add_argument(
        '--tmux-panes', '-p', default=6, metavar="PANES",
        help="Max tmux panes per window (default: 6)")
    parser.add_argument(
        '--tmux-sync', '-S', action='store_true',
        help="Run tmux's set-option synchronize-panes on each tmux window")
    parser.add_argument(
        '--tmux-session', '-t', default='intmux', metavar="SESSION",
        help="tmux session name (default: intmux)")

    subparsers = parser.add_subparsers(help='sub-command help', dest='subcommand')

    ssh_parser = subparsers.add_parser(
        'ssh', help='Connect to hosts via SSH',
        description='Connect to the provided hosts.')
    ssh_parser.add_argument(
        '--options', '-o', default="", help="Options to pass to connection.")
    ssh_parser.add_argument('hosts', nargs='*', help="Host names to connect to")

    docker_parser = subparsers.add_parser(
        'docker', help='Connect to docker containers',
        description='Connect to the provided running containers')
    docker_parser.add_argument(
        '--shell', default='sh', help='Command to execute on docker container (default: sh)')
    docker_parser.add_argument(
        'hosts', nargs='*',
        help="List of docker containers to connect to (default: connect to all local docker containers)")

    composer_parser = subparsers.add_parser(
        'compose', help='Connect to docker containers via docker-compose',
        description=(
            'Connect to all running containers associated with the docker-compose '
            'in the current directory.'))
    composer_parser.add_argument(
        '--shell', default='sh', help='Command to execute on docker container (default: sh)')

    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log))

    if not args.subcommand:
        print('You must supply a subcommand.')
        sys.exit(posix.EX_USAGE)

    session = tmux.TmuxSession(args)
    session.connect()

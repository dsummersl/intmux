from __future__ import print_function

import argparse
import logging
import os.path
import subprocess
import sys

from . import connections

logger = logging.getLogger('intmux')


def tmux(command):
    """ Run a tmux command """
    command = "tmux {}".format(command)
    logger.debug('tmux "{}"'.format(command))
    subprocess.check_call([command], shell=True)


def new_session(session):
    """ Create a new tmux session"""
    # TODO verify that the session doesn't already exist.
    command = "tmux new-session -d -s '{}'".format(session)
    logger.debug('new_session "{}"'.format(command))
    subprocess.check_call([command], shell=True)


def main():
    parser = argparse.ArgumentParser(
        description="Connect to several hosts in a tmux session."
    )

    parser.add_argument(
        '--command', '-c', default="", help="Command to execute when connecting to a remote host")
    parser.add_argument(
        '--input', '-i', nargs='?', type=argparse.FileType('r'), default=None,
        help="Read list of hosts from input file.")
    parser.add_argument(
        '--log', '-l', default="WARN", help="Log level (default: WARN)")
    parser.add_argument(
        '--panes', '-p', default=6, help="Max panes per window (default: 6)")
    parser.add_argument(
        '--script', '-s', default="", help="Execute commands in local file remotely")
    parser.add_argument(
        '--sync', '-S', action='store_true',
        help="Run set-option synchronize-panes on each tmux window")
    parser.add_argument(
        '--tmux', '-t', default='intmux', help="tmux session name (default: intmux)")

    subparsers = parser.add_subparsers(help='sub-command help', dest='subcommand')

    ssh_parser = subparsers.add_parser('ssh', help='Connect to hosts via SSH')
    ssh_parser.add_argument(
        '--options', '-o', default="", help="Options to pass to connection.")
    ssh_parser.add_argument('hosts', nargs='*', help="Host names to connect to")

    docker_parser = subparsers.add_parser('docker', help='Connect to docker containers')
    docker_parser.add_argument('--shell', default='sh', help='Command to execute on docker container (default: sh)')
    docker_parser.add_argument(
        'hosts', nargs='*',
        help="List of docker containers to connect to (default: connect to all local docker containers)")

    compose_parser = subparsers.add_parser('compose', help='Connect to docker containers via docker-compose')
    compose_parser.add_argument('hosts', nargs='*', help="docker-compose hosts to connect to.")

    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log))

    if not args.subcommand:
        print('You must supply a subcommand.')
        sys.exit(1)

    if args.subcommand == 'ssh':
        connection_type = connections.SSHConnection
    elif args.subcommand == 'docker':
        connection_type = connections.DockerConnection
    else:
        print('Unknown subcommand type!')
        sys.exit(1)

    if args.input:
        hosts = []
        for line in args.input.readlines():
            hosts.append(line[:-1])

    new_session(args.tmux)

    # turn on window activity notification:
    tmux("set-window-option -t {} -g monitor-activity on".format(args.tmux))
    tmux("set-option -t {} -g visual-activity on".format(args.tmux))

    cnt = 0
    wcnt = 0
    first = 1
    made_new_window = True
    for host in connection_type.hosts(args):
        logger.debug('Host = {}'.format(host))
        if cnt < args.panes or args.panes == 0:
            if first == 0:
                tmux("split-window -t {}".format("{}:{}".format(args.tmux, wcnt)))
            first = 0
            cnt = cnt + 1
        else:
            if made_new_window and args.sync:
                tmux("set-option -t {}:{} synchronize-panes".format(args.tmux, wcnt))
                made_new_window = False
            made_new_window = True
            cnt = cnt + 1
            wcnt = wcnt + 1
            cnt = 1
            tmux("new-window -t {}".format(args.tmux))
            tmux("rename-window -t {}:{} {}".format(args.tmux, wcnt, host))
            tmux("set-window-option -t {}:{} allow-rename off".format(args.tmux, wcnt))

        if args.script and not os.path.exists(args.script):
            print("{} does not exist!".format(args.script))
            sys.exit(1)

        if args.script:
            tmux("send-keys -t {}:{} \"{}\" C-m".format(
                args.tmux, wcnt, connection_type.copy(host, args)))

        tmux("send-keys -t {}:{} \"{}\" C-m".format(
            args.tmux, wcnt, connection_type.connect(host, args)))

        if args.command:
            tmux("send-keys -t {}:{} {} C-m".format(args.tmux, wcnt, args.command))

        if args.script:
            basename = os.path.basename(args.script)
            tmux("send-keys -t {}:{} 'chmod u+x /tmp/{} && /tmp/{}' C-m".format(args.tmux, wcnt, basename, basename))

        tmux("select-layout -t {}:{} tiled".format(args.tmux, wcnt))

    if made_new_window and args.sync:
        logger.debug('synchronizing last window')
        tmux("set-option -t {}:{} synchronize-panes".format(args.tmux, wcnt))

    # remove session 0 - which is not connected to anything
    # TODO provide a hotkey to run in all sessions

    # Detect if we are already in a session. If we are, just switch to the other
    # session:
    if 'TMUX' in os.environ:
        # When quitting out of this session, just switch to some other client
        # (since there appears to be one already)
        tmux("set-option -g detach-on-destroy off")
        tmux("switch-client -t {}:{}".format(args.tmux, wcnt))
    else:
        tmux("attach-session -t {}:{}".format(args.tmux, wcnt))

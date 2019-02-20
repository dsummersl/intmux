import logging
import os.path
import posix
import subprocess
import sys

from . import connections

logger = logging.getLogger('tmux')


def tmux(command):
    """ Run a tmux command """
    command = "tmux {}".format(command)
    logger.debug('tmux "{}"'.format(command))
    subprocess.check_call([command], shell=True)


def new_session(session):
    """ Create a new tmux session"""
    sessions = connections.check_output_as_list('tmux list-sessions -F "#S"')
    if session in sessions:
        print("Session '{}' already exists!".format(session))
        sys.exit(posix.EX_USAGE)

    command = "tmux new-session -d -s '{}'".format(session)
    logger.debug('new_session "{}"'.format(command))
    subprocess.check_call([command], shell=True)


class TmuxSession(object):

    def __init__(self, args):
        self.args = args
        self.session = args.tmux_session
        self.panes = args.tmux_panes
        self.sync = not args.tmux_no_sync
        self.command = args.command
        self.script = args.script

        if args.script and not os.path.exists(args.script):
            print("{} does not exist!".format(args.script))
            sys.exit(posix.EX_USAGE)

        if args.subcommand == 'ssh':
            self.connection_type = connections.SSHConnection
        elif args.subcommand == 'docker':
            self.connection_type = connections.DockerConnection
        elif args.subcommand == 'compose':
            self.connection_type = connections.DockerComposeConnection
        elif args.subcommand == 'ssh-docker':
            self.connection_type = connections.SSHDockerConnection
        else:
            print('Unknown subcommand type!')
            sys.exit(posix.EX_USAGE)

        self.hosts = []
        # Read hosts from stdin
        if not sys.stdin.isatty():
            for line in sys.stdin.readlines():
                self.hosts.append(line[:-1])
            logger.debug('STDIN hosts = {}'.format(self.hosts))
        elif args.input:
            for line in args.input.readlines():
                self.hosts.append(line[:-1])
            logger.debug('--input hosts = {}'.format(self.hosts))
        else:
            try:
                self.hosts = self.connection_type.hosts(args)
            except ValueError as e:
                print(e)
                sys.exit(posix.EX_USAGE)
            logger.debug('connection hosts = {}'.format(self.hosts))

        if len(self.hosts) == 0:
            print("At least one host must be specified!\n")
            sys.exit(posix.EX_USAGE)

    def connect(self):
        new_session(self.session)

        # turn on window activity notification:
        tmux("set-window-option -t {} -g monitor-activity on".format(self.session))
        tmux("set-option -t {} -g visual-activity on".format(self.session))

        cnt = 0
        wcnt = 0
        first = 1
        made_new_window = True
        for host in self.hosts:
            logger.debug('Host = {}'.format(host))
            # if hostname is '\n' then make a new window
            if host != '\n' and (cnt < self.panes or self.panes == 0):
                if first == 0:
                    tmux("split-window -t {}".format("{}:{}".format(self.session, wcnt)))
                first = 0
                cnt = cnt + 1
            else:
                if made_new_window and self.sync:
                    tmux("set-option -t {}:{} synchronize-panes".format(self.session, wcnt))
                    made_new_window = False
                made_new_window = True
                wcnt = wcnt + 1
                cnt = 1
                tmux("new-window -t {}".format(self.session))
                tmux("rename-window -t {}:{} {}".format(self.session, wcnt, host))
                tmux("set-window-option -t {}:{} allow-rename off".format(self.session, wcnt))

            if self.script:
                tmux("send-keys -t {}:{} \"{}\" C-m".format(
                    self.session, wcnt, self.connection_type.copy(host, self.args)))
            elif self.command:
                tmux("send-keys -t {}:{} \"{}\" C-m".format(
                    self.session, wcnt, self.connection_type.command(host, self.args)))
            else:
                tmux("send-keys -t {}:{} \"{}\" C-m".format(
                    self.session, wcnt, self.connection_type.connect(host, self.args)))

            tmux("select-layout -t {}:{} tiled".format(self.session, wcnt))

        if made_new_window and self.sync:
            logger.debug('synchronizing last window')
            tmux("set-option -t {}:{} synchronize-panes".format(self.session, wcnt))

        # remove session 0 - which is not connected to anything
        # TODO provide a hotkey to run in all sessions

        # Detect if we are already in a session. If we are, just switch to the other
        # session:
        if 'TMUX' in os.environ:
            # When quitting out of this session, just switch to some other client
            # (since there appears to be one already)
            tmux("set-option -g detach-on-destroy off")
            tmux("switch-client -t {}:{}".format(self.session, wcnt))
        else:
            tmux("attach-session -t {}:{}".format(self.session, wcnt))

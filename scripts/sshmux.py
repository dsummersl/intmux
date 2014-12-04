import argparse
import logging
import subprocess
import sys

logger = logging.getLogger('shmux')

def tmux(command):
	""" Run a tmux command """
	command = "tmux {}".format(command)
	logger.debug('tmux "{}"'.format(command))
	subprocess.check_call([command],shell=True)

def new_session(session):
	""" Create a new tmux session"""
	# TODO verify that the session doesn't already exist.
	command = "tmux new-session -d -s '{}'".format(session)
	logger.debug('new_session "{}"'.format(command))
	subprocess.check_call([command],shell=True)

def main():
	parser = argparse.ArgumentParser(
		description="Connect to several hosts with SSH in a new tmux session."
	)
	parser.add_argument('--input','-i',nargs='?',type=argparse.FileType('r'),default=None,help="Read list of hosts from input file.")
	parser.add_argument('--log','-l',default="WARN", help="Log level (default: WARN)")
	parser.add_argument('--options','-o',default="", help="Options to pass to ssh command.")
	parser.add_argument('--panes','-p',default=6, help="Max SSH panes per window (default: 6)")
	parser.add_argument('--session','-s',default='shmux', help="tmux session name (default: shmux)")
	parser.add_argument('--sync','-S', action='store_true',help="Run set-option synchronize-panes on each tmux window")
	parser.add_argument('hosts',nargs='*', help="Host names to connect to")
	args = parser.parse_args()
	logging.basicConfig(level=getattr(logging,args.log))
	hosts = args.hosts

	if args.input:
		hosts = []
		for line in args.input.readlines():
			hosts.append(line[:-1])
	elif len(args.hosts) == 0:
		print "At least one host must be specified!\n"
		sys.exit(1)

	new_session(args.session)

	# turn on window activity notification:
	tmux("set-window-option -t {} -g monitor-activity on".format(args.session))
	tmux("set-option -t {} -g visual-activity on".format(args.session))

	#tmux bind-key e command-prompt -p "message?" "run-shell \"./lib/execute_everywhere.sh '%1'\""

	cnt=0
	wcnt=0
	first=1
	madeNewWindow = True
	for host in hosts:
		logger.debug('Host = {}'.format(host))
		if cnt < args.panes or args.panes == 0:
			if first == 0:
				tmux("split-window -t {}".format("{}:{}".format(args.session,wcnt)))
			first=0
			cnt=cnt+1
		else:
			madeNewWindow = True
			cnt=cnt+1
			wcnt=wcnt+1
			cnt=1
			if madeNewWindow and args.sync:
				tmux("set-option -t {}:{} synchronize-panes".format(args.session,wcnt))
				madeNewWindow = False
			tmux("new-window -t {}:{}".format(args.session,wcnt))
			tmux("rename-window -t {}:{} {}".format(args.session,wcnt,host))
			tmux("set-window-option -t {}:{} allow-rename off".format(args.session,wcnt))

		tmux("send-keys -t {}:{} \"ssh {} {}\" C-m".format(args.session,wcnt,args.options,host))
		tmux("select-layout -t {}:{} tiled".format(args.session,wcnt))

	if madeNewWindow and args.sync:
		tmux("set-option -t {}:{} synchronize-panes".format(args.session,wcnt))

	# remove session 0 - which is not connected to anything
	# TODO provide a hotkey to run in all sessions

	tmux("attach-session -t {}:{}".format(args.session,wcnt))

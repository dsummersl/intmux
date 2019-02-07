Introduction
============

A command line application to connect to multiple hosts within a tmux session.

Supports connections to SSH hosts, local docker and docker-compose.

**SSH**

By default intmux will open up to six hosts in a new tmux session. For example,
the following command creates a new tmux session with two windows (one ssh'd to
host1, another to user@host2):

    intmux ssh host1 user@host2
    intmux -i inputfile.txt ssh

One could use the `--sync` option to enable tmux's 'synchronized-panes' setting:

    intmux --sync ssh host1 host2 host3

**Docker**

intmux can also be used to connect to all running docker instances:

    intmux docker

Or connect to specific containers:

    intmux docker a7e8a0b392ea f947ff94a995

**Docker-compose**

All running services of the docker-compose in your current working directory can
also be connected to:

    intmux compose


Installation
------------

Execute:

    pip install intmux

Help
----

    intmux --help

    usage: intmux [-h] [--command COMMAND] [--input [INPUT]] [--log LOG]
                  [--panes PANES] [--script SCRIPT] [--sync] [--tmux TMUX]
                  {ssh,docker,compose} ...

    Connect to several hosts in a tmux session.

    positional arguments:
      {ssh,docker,compose}  sub-command help
        ssh                 Connect to hosts via SSH
        docker              Connect to docker containers
        compose             Connect to docker containers via docker-compose

    optional arguments:
      -h, --help            show this help message and exit
      --command COMMAND, -c COMMAND
                            Command to execute when connecting to a remote host
      --input [INPUT], -i [INPUT]
                            Read list of hosts from input file.
      --log LOG, -l LOG     Log level (default: WARN)
      --panes PANES, -p PANES
                            Max panes per window (default: 6)
      --script SCRIPT, -s SCRIPT
                            Execute commands in local file remotely
      --sync, -S            Run set-option synchronize-panes on each tmux window
      --tmux TMUX, -t TMUX  tmux session name (default: intmux)

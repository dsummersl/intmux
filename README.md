Introduction
============

A command line application to connect to multiple hosts within a tmux session.

Usage:

    intmux ssh host1 user@host2
    intmux -i inputfile.txt ssh

Help:

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

Installation
------------

Execute:

    sudo python setup.py install

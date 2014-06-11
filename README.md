Introduction
============

A simple command line application to connect to multiple hosts within one tmux
session. Useful for executing the same command across multiple hosts, for
example.

Usage:

    sshmux host1 user@host2
    sshmux -i inputfile.txt

Help:

    › sshmux -h
    usage: sshmux [-h] [--input [INPUT]] [--log LOG] [--panes PANES]
                  [--session SESSION] [--sync]
                  [hosts [hosts ...]]

    Connect to several hosts with SSH in a new tmux session.

    positional arguments:
      hosts                 Host names to connect to

    optional arguments:
      -h, --help            show this help message and exit
      --input [INPUT], -i [INPUT]
                            Read list of hosts from input file.
      --log LOG, -l LOG     Log level (default: WARN)
      --panes PANES, -p PANES
                            Max SSH panes per window (default: 6)
      --session SESSION, -s SESSION
                            tmux session name (default: shmux)
      --sync, -S            Run set-option synchronize-panes on each tmux window

Installation
------------

Execute:

  sudo python setup.py install

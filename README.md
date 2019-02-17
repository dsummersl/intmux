Introduction
============

Connect to multiple ssh/docker hosts "in tmux".

intmux is a command line application to connect to multiple ssh/docker hosts
within a tmux session. Supports connections to SSH hosts, local docker and
docker-compose.

**SSH**

By default intmux will open up to six hosts in a new tmux session. For example,
the following command creates a new tmux session with two windows (one ssh'd to
host1, another to user@host2):

    intmux ssh host1 user@host2
    intmux -i inputfile.txt ssh

One could use the `--sync` option to enable tmux's 'synchronized-panes' setting:

    intmux --sync ssh host1 host2 host3

**Docker**

intmux can also be used to connect to all running local docker instances:

    # Connect to all local containers
    intmux docker

    # Connect to specific containers
    intmux docker a_name f947ff94a995

    # Look at logs on hosts:
    intmux docker --docker-command 'logs -f' a_name f947ff94a995

Docker containers can also be connected to over SSH:

    # Connect to all remote containers on two different hosts
    intmux ssh-docker host1 user@host2

    # Connect to specific containers
    intmux ssh-docker --docker-containers "a_name,f947ff94a995" host1 user@host2

    # Look at logs on hosts:
    intmux ssh-docker --docker-command 'logs -f' --docker-containers "a_name,f947ff94a995" host1 user@host2

**Docker-compose**

All running services of the docker-compose in your current working directory can
also be connected to:

    # Connect to all containers
    intmux compose

    # Connect to specific containers:
    intmux compose db web


Installation
------------

Execute:

    pip install intmux

Help
----


Main help:

    intmux --help

    usage: intmux [-h] [--log LOG] [--command COMMAND] [--input INPUT]
                  [--script SCRIPT] [--tmux-panes PANES] [--tmux-sync]
                  [--tmux-session SESSION]
                  {ssh,docker,ssh-docker,compose} ...

    Connect to several hosts in a tmux session.

    positional arguments:
      {ssh,docker,ssh-docker,compose}
                            sub-command help
        ssh                 Connect to hosts via SSH
        docker              Connect to docker containers via 'docker exec'
        ssh-docker          Connect to docker containers on remote SSH hosts
        compose             Connect to docker containers associated with current
                            docker-compose via 'docker exec'

    optional arguments:
      -h, --help            show this help message and exit
      --log LOG, -l LOG     Log level (default: WARN)
      --command COMMAND, -c COMMAND
                            Command to execute when connecting to a remote host
      --input INPUT, -i INPUT
                            Read list of hosts from input file when provided,
                            otherwise from STDIN.
      --script SCRIPT, -s SCRIPT
                            Execute commands in local file remotely
      --tmux-panes PANES, -p PANES
                            Max tmux panes per window (default: 6)
      --tmux-sync, -S       Run tmux's set-option synchronize-panes on each tmux
                            window
      --tmux-session SESSION, -t SESSION
                            tmux session name (default: intmux)

SSH help:

    intmux ssh -h

    usage: intmux ssh [-h] [--ssh-options SSH_OPTIONS] [hosts [hosts ...]]

    Connect to the provided hosts.

    positional arguments:
      hosts                 SSH hosts to connect to.

    optional arguments:
      -h, --help            show this help message and exit
      --ssh-options SSH_OPTIONS, -so SSH_OPTIONS
                            Options to pass to SSH connection.

Docker help:

    intmux docker -h

    usage: intmux docker [-h] [--docker-command DOCKER_COMMAND] [--approximate]
                         [hosts [hosts ...]]

    Connect to the provided running containers

    positional arguments:
      hosts                 List of docker containers to connect to (default:
                            connect to all containers)

    optional arguments:
      -h, --help            show this help message and exit
      --docker-command DOCKER_COMMAND, -dc DOCKER_COMMAND
                            Docker command to execute (default: 'exec -it {}
                            bash'). If '{}' is included in the command, the docker
                            host is substituted there, the host is appended. NOTE:
                            may invalidate any --script/--command parameters if a
                            shell is not provided.
      --approximate, -a     Include any docker container names that only partially
                            match hosts.

Docker Compose help:

    intmux compose -h

    usage: intmux compose [-h] [--docker-command DOCKER_COMMAND] [--approximate]
                          [hosts [hosts ...]]

    Connect to containers associated with the docker-compose in the current
    directory.

    positional arguments:
      hosts                 List of docker containers to connect to (default:
                            connect to all containers)

    optional arguments:
      -h, --help            show this help message and exit
      --docker-command DOCKER_COMMAND, -dc DOCKER_COMMAND
                            Docker command to execute (default: 'exec -it {}
                            bash'). If '{}' is included in the command, the docker
                            host is substituted there, the host is appended.
      --approximate, -a     Include any docker container names that only partially
                            match hosts.
SSH Docker help:

    intmux ssh-docker -h

    usage: intmux ssh-docker [-h] [--ssh-options SSH_OPTIONS]
                             [--docker-containers DOCKER_CONTAINERS]
                             [--docker-command DOCKER_COMMAND] [--approximate]
                             [hosts [hosts ...]]

    Connect to docker containers on provided SSH hosts

    positional arguments:
      hosts                 SSH hosts to connect to.

    optional arguments:
      -h, --help            show this help message and exit
      --ssh-options SSH_OPTIONS, -so SSH_OPTIONS
                            Options to pass to SSH connection.
      --docker-containers DOCKER_CONTAINERS, -dC DOCKER_CONTAINERS
                            Comma separated list of docker containers to connect
                            to (default: connect to all containers)
      --docker-command DOCKER_COMMAND, -dc DOCKER_COMMAND
                            Docker command to execute (default: 'exec -it {}
                            bash'). If '{}' is included in the command, the docker
                            host is substituted there, the host is appended. NOTE:
                            may invalidate any --script/--command parameters if a
                            shell is not provided.
      --approximate, -a     Include any docker container names that only partially
                            match hosts.

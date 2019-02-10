import logging
import posix
import subprocess
import sys

logger = logging.getLogger('connections')


def check_output_as_list(command):
    logger.debug(command)
    output = subprocess.check_output([command], shell=True)
    lines = str(output, 'utf-8').split('\n')
    lines = [line for line in lines if len(line) > 0]
    logger.debug(lines)
    return lines


class Connection(object):
    @classmethod
    def hosts(cls, args):
        raise NotImplementedError()

    @classmethod
    def copy(cls, host, args):
        raise NotImplementedError()

    @classmethod
    def connect(cls, host, args):
        raise NotImplementedError()


class SSHConnection(Connection):
    @classmethod
    def hosts(cls, args):
        if len(args.hosts) == 0:
            print("At least one host must be specified!\n")
            sys.exit(posix.EX_USAGE)
        return args.hosts

    @classmethod
    def copy(cls, host, args):
        return 'scp {} {} {}:/tmp'.format(args.options, args.script, host)

    @classmethod
    def connect(cls, host, args):
        return 'ssh {} {}'.format(args.options, host)


class DockerConnection(Connection):
    @classmethod
    def hosts(cls, args):
        hosts = args.hosts
        if len(hosts) == 0:
            command = 'docker ps -q'
            hosts = check_output_as_list(command)

        logger.debug("hosts = {0}".format(hosts))

        if len(hosts) == 0:
            print("No docker containers detected to connect to!")
            sys.exit(posix.EX_USAGE)

        return hosts

    @classmethod
    def copy(cls, host, args):
        return 'docker cp {} {}:/tmp'.format(args.script, host)

    @classmethod
    def connect(cls, host, args):
        if args.attach:
            return 'docker attach {}'.format(host)
        else:
            return 'docker exec -it {} {}'.format(host, args.shell)


class DockerComposeConnection(DockerConnection):
    @classmethod
    def hosts(cls, args):
        containers = check_output_as_list('docker-compose ps --filter="status=running" --services')
        logger.debug('containers = "{}"'.format(containers))

        filtered_hosts = []
        for host in args.hosts:
            logger.debug('filtered_name = "{}"'.format(host))
            if host not in containers:
                print("No such service '{}' in {}".format(host, containers))
                sys.exit(posix.EX_USAGE)
            filtered_hosts.append(host)
        logger.debug('filtered_hosts = "{}"'.format(filtered_hosts))

        hosts = []
        for name in containers:
            if len(filtered_hosts) > 0 and name not in filtered_hosts:
                continue
            container = check_output_as_list('docker-compose ps -q {}'.format(name))
            if len(container) == 1:
                hosts.append(container[0])

        if len(hosts) == 0:
            print("No running docker containers detected to connect to!")
            sys.exit(posix.EX_USAGE)

        return hosts

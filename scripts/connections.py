import logging
import subprocess
from contextlib import contextmanager
from os import path

logger = logging.getLogger('connections')


@contextmanager
def set_argument(parsed_args, name, value):
    old_value = getattr(parsed_args, name)
    setattr(parsed_args, name, value)
    try:
        yield parsed_args
    finally:
        setattr(parsed_args, name, old_value)


def check_output_as_list(command):
    logger.debug(command)
    output = subprocess.check_output([command], shell=True)
    logger.debug(output)
    lines = output.decode('utf-8').split('\n')
    lines = [line for line in lines if len(line) > 0]
    logger.debug(lines)
    return lines


class Connection(object):
    @classmethod
    def hosts(cls, parsed_args):
        """ Returns a list of hosts to connect to.

        Can return a host as '\n' to force tmux to make a new window.
        """
        raise NotImplementedError()

    @classmethod
    def copy(cls, host, parsed_args):
        raise NotImplementedError()

    @classmethod
    def command(cls, host, parsed_args):
        raise NotImplementedError()

    @classmethod
    def connect(cls, host, parsed_args):
        raise NotImplementedError()


class SSHConnection(Connection):
    @classmethod
    def hosts(cls, parsed_args):
        if len(parsed_args.hosts) == 0:
            raise ValueError("At least one host must be specified!\n")
        return parsed_args.hosts

    @classmethod
    def copy(cls, host, parsed_args, and_execute=True):
        script_path, script_name = path.split(parsed_args.script)
        copy = 'scp {} {} {}:/tmp'.format(parsed_args.ssh_options, parsed_args.script, host)
        connect = cls.connect(host, parsed_args)
        chmod = connect + ' chmod u+x /tmp/{}'.format(script_name)
        if and_execute:
            execute = connect + ' /tmp/{}'.format(script_name)
            return '{} && {} && {} && {}'.format(copy, chmod, execute, connect)
        return '{} && {}'.format(copy, chmod)

    @classmethod
    def command(cls, host, parsed_args):
        return 'ssh {} {} {}'.format(parsed_args.ssh_options, host, parsed_args.command)

    @classmethod
    def connect(cls, host, parsed_args):
        return 'ssh {} {}'.format(parsed_args.ssh_options, host)


class DockerConnection(Connection):
    @classmethod
    def hosts(cls, parsed_args, prepend_command=''):
        host_names = parsed_args.hosts
        matched_host_names = {}
        for name in host_names:
            matched_host_names[name] = False
        hosts = []
        names_and_ids = check_output_as_list(
            prepend_command + "docker ps --format '{{.Names}},{{.ID}}'")
        if len(host_names) == 0:
            hosts.extend(n_and_i.split(',')[1] for n_and_i in names_and_ids)
        else:
            for n_and_i in names_and_ids:
                n, i = n_and_i.split(',')
                if n in host_names:
                    hosts.append(i)
                    matched_host_names[n] = True
                elif i in host_names:
                    hosts.append(i)
                    matched_host_names[n] = True
                elif parsed_args.approximate and any(name in n for name in host_names):
                    hosts.append(i)
                elif parsed_args.approximate and any(name in i for name in host_names):
                    hosts.append(i)

        logger.debug("hosts = {0}".format(hosts))

        if len(hosts) == 0:
            raise ValueError("No docker containers detected to connect to!")
        if not parsed_args.approximate:
            for name in host_names:
                if not matched_host_names[name]:
                    raise ValueError("No container named '{}' found!".format(name))

        return hosts

    @classmethod
    def _execute(cls, host, parsed_args, command, prepend_command=''):
        with set_argument(parsed_args, 'docker_command', 'exec -it {}'.format('{} ' + command)) as parsed_args:
            return cls.connect(host, parsed_args, prepend_command)

    @classmethod
    def copy(cls, host, parsed_args, prepend_command=''):
        script_path, script_name = path.split(parsed_args.script)
        copy = '{}docker cp {} {}:/tmp'.format(prepend_command, parsed_args.script, host)
        chmod = cls._execute(host, parsed_args, 'chmod u+x /tmp/' + script_name, prepend_command)
        execute = cls._execute(host, parsed_args, '/tmp/' + script_name, prepend_command)
        connect = cls.connect(host, parsed_args, prepend_command)
        return '{} && {} && {} && {}'.format(copy, chmod, execute, connect)

    @classmethod
    def command(cls, host, parsed_args, prepend_command=''):
        command = cls._execute(host, parsed_args, parsed_args.command, prepend_command)
        connect = cls.connect(host, parsed_args, prepend_command)
        return '{} && {}'.format(command, connect)

    @classmethod
    def connect(cls, host, parsed_args, prepend_command=''):
        if parsed_args.docker_command:
            if '{}' in parsed_args.docker_command:
                # Commands like:
                #  -dc 'exec -it {} bash'
                return '{}docker {}'.format(prepend_command, parsed_args.docker_command.format(host))
            else:
                # Commands without {} get host appended to it, like:
                #  -dc logs
                #  -dc 'logs -f'
                return '{}docker {} {}'.format(prepend_command, parsed_args.docker_command, host)
        else:
            return '{}docker exec -it {} bash'.format(prepend_command, host)


class DockerComposeConnection(DockerConnection):
    @classmethod
    def hosts(cls, parsed_args):
        containers = check_output_as_list('docker-compose ps --filter="status=running" --services')
        logger.debug('containers = "{}"'.format(containers))

        filtered_hosts = []
        for container_name in containers:
            if container_name in parsed_args.hosts:
                filtered_hosts.append(container_name)
            elif parsed_args.approximate and any(h in container_name for h in parsed_args.hosts):
                filtered_hosts.append(container_name)

        logger.debug('filtered_hosts = "{}"'.format(filtered_hosts))
        if len(filtered_hosts) == 0:
            raise ValueError("No service found in {}".format(containers))

        hosts = []
        for name in containers:
            if len(filtered_hosts) > 0 and name not in filtered_hosts:
                continue
            container = check_output_as_list('docker-compose ps -q {}'.format(name))
            if len(container) == 1:
                hosts.append(container[0])

        if len(hosts) == 0:
            raise ValueError("No running docker containers detected to connect to!")

        return hosts


class SSHDockerConnection(DockerConnection):
    @classmethod
    def hosts(cls, parsed_args):
        if len(parsed_args.hosts) == 0:
            raise ValueError("At least one host must be specified!\n")

        ssh_hosts = parsed_args.hosts

        with set_argument(parsed_args, 'hosts', parsed_args.docker_containers.split(',')) as parsed_args:
            hosts = []
            for ssh_host in ssh_hosts:
                found_containers = super().hosts(parsed_args, 'ssh {} '.format(ssh_host))
                more_hosts = ['{},{}'.format(ssh_host, container) for container in found_containers]
                if len(hosts) > 0 and len(more_hosts) > 0:
                    hosts.append('\n')
                hosts.extend(more_hosts)

            return hosts

    @classmethod
    def copy(cls, host, parsed_args):
        ssh_host, container = host.split(',')
        ssh_copy = SSHConnection.copy(ssh_host, parsed_args, and_execute=False)
        with set_argument(parsed_args, 'ssh_options', '-t ' + parsed_args.ssh_options) as parsed_args:
            ssh_command = SSHConnection.connect(ssh_host, parsed_args)
        with set_argument(parsed_args, 'script', '/tmp/' + parsed_args.script) as parsed_args:
            docker_copy = DockerConnection.copy(container, parsed_args, prepend_command=ssh_command + ' ')
        return '{} && {}'.format(ssh_copy, docker_copy)

    @classmethod
    def command(cls, host, parsed_args, prepend_command=''):
        ssh_host, container = host.split(',')
        with set_argument(parsed_args, 'ssh_options', '-t ' + parsed_args.ssh_options) as parsed_args:
            ssh_command = SSHConnection.connect(ssh_host, parsed_args)
            return DockerConnection.command(container, parsed_args, prepend_command=ssh_command + ' ')

    @classmethod
    def connect(cls, host, parsed_args):
        ssh_host, container = host.split(',')
        with set_argument(parsed_args, 'ssh_options', '-t ' + parsed_args.ssh_options) as parsed_args:
            ssh_command = SSHConnection.connect(ssh_host, parsed_args)
            return DockerConnection.connect(container, parsed_args, prepend_command=ssh_command + ' ')

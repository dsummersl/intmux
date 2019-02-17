import logging
import subprocess

logger = logging.getLogger('connections')


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
            raise ValueError("At least one host must be specified!\n")
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
        host_names = args.hosts
        hosts = []
        names_and_ids = check_output_as_list("docker ps --format '{{.Names}},{{.ID}}'")
        if len(host_names) == 0:
            hosts.extend(n_and_i.split(',')[1] for n_and_i in names_and_ids)
        else:
            for n_and_i in names_and_ids:
                n, i = n_and_i.split(',')
                if n in host_names:
                    hosts.append(i)
                elif i in host_names:
                    hosts.append(i)
                elif args.approximate and any(name in n for name in host_names):
                    hosts.append(i)
                elif args.approximate and any(name in i for name in host_names):
                    hosts.append(i)

        logger.debug("hosts = {0}".format(hosts))

        if len(hosts) == 0:
            raise ValueError("No docker containers detected to connect to!")

        return hosts

    @classmethod
    def copy(cls, host, args):
        return 'docker cp {} {}:/tmp'.format(args.script, host)

    @classmethod
    def connect(cls, host, args):
        if args.docker_command:
            if '{}' in args.docker_command:
                # Commands like:
                #  -dc 'exec -it {} bash'
                return 'docker {}'.format(args.docker_command.format(host))
            else:
                # Commands without {} get host appended to it, like:
                #  -dc logs
                #  -dc 'logs -f'
                return 'docker {} {}'.format(args.docker_command, host)
        else:
            return 'docker exec -it {} bash'.format(host)


class DockerComposeConnection(DockerConnection):
    @classmethod
    def hosts(cls, args):
        containers = check_output_as_list('docker-compose ps --filter="status=running" --services')
        logger.debug('containers = "{}"'.format(containers))

        filtered_hosts = []
        for container_name in containers:
            if container_name in args.hosts:
                filtered_hosts.append(container_name)
            elif args.approximate and any(h in container_name for h in args.hosts):
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

class Connection(object):
    @classmethod
    def copy(cls, host, args):
        raise NotImplementedError()

    @classmethod
    def connect(cls, host, args):
        raise NotImplementedError()


class SSHConnection(Connection):
    @classmethod
    def copy(cls, host, args):
        return 'scp {} {} {}:/tmp'.format(args.options, args.script, host)

    @classmethod
    def connect(cls, host, args):
        return 'ssh {} {}'.format(args.options, host)


class DockerConnection(Connection):
    # TODO support * to do all docker containers.
    @classmethod
    def copy(cls, host, args):
        return 'docker cp {} {}:/tmp'.format(args.script, host)

    @classmethod
    def connect(cls, host, args):
        return 'docker exec -it {} bash'.format(host)

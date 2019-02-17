import pytest
from mock import MagicMock, patch
from scripts import connections


@patch('scripts.connections.check_output_as_list')
class TestDockerConnection:
    docker_containers = ['one,containerid1', 'two,containerid2']

    def _setup_sife_effect(self, output_mock):
        def side_effect(*args, **kwargs):
            if args[0] == "docker ps --format '{{.Names}},{{.ID}}'":
                return self.docker_containers
        output_mock.side_effect = side_effect

    def test_hosts_no_containers(self, output_mock):
        """ When there are no containers or process response, well, no hosts!  """
        with pytest.raises(ValueError):
            connections.DockerConnection.hosts(MagicMock())

    def test_no_hosts(self, output_mock):
        """ When no args.hosts are passed, return all running containers """
        self._setup_sife_effect(output_mock)

        hosts = connections.DockerConnection.hosts(MagicMock())
        assert hosts == ['containerid1', 'containerid2']

    def test_hosts(self, output_mock):
        args = MagicMock()
        args.hosts = ['ahost']

        self._setup_sife_effect(output_mock)

        # if the hostname doesn't match anything, nothing is returned
        with pytest.raises(ValueError):
            connections.DockerConnection.hosts(args)

        # If the hostname does match one, return it
        args.hosts = ['one']
        assert ['containerid1'] == connections.DockerConnection.hosts(args)

        # If the hostname matches both, return both
        args.hosts = ['two', 'one']
        assert ['containerid1', 'containerid2'] == connections.DockerConnection.hosts(args)

        # Matches on IDs as well
        args.hosts = ['containerid1']
        assert ['containerid1'] == connections.DockerConnection.hosts(args)

    def test_hosts_approximate(self, output_mock):
        args = MagicMock()
        args.hosts = ['wo']
        args.approximate = True

        self._setup_sife_effect(output_mock)
        assert ['containerid2'] == connections.DockerConnection.hosts(args)

        args.hosts = ['o']
        assert ['containerid1', 'containerid2'] == connections.DockerConnection.hosts(args)

        args.hosts = ['blah']
        with pytest.raises(ValueError):
            connections.DockerConnection.hosts(args)

        args.hosts = ['wo', 'blah']
        assert ['containerid2'] == connections.DockerConnection.hosts(args)

    def test_connect(self, output_mock):
        args = MagicMock()
        args.hosts = ['containerid1']
        args.approximate = False
        args.docker_command = ''

        self._setup_sife_effect(output_mock)
        assert 'docker exec -it containerid1 bash' == \
            connections.DockerConnection.connect('containerid1', args)

    def test_command(self, output_mock):
        args = MagicMock()
        args.hosts = ['host1']
        args.approximate = False
        args.docker_command = ''
        args.command = 'pwd'

        self._setup_sife_effect(output_mock)
        assert 'docker exec -it containerid1 pwd && docker exec -it containerid1 bash' == \
            connections.DockerConnection.command('containerid1', args)

    def test_copy(self, output_mock):
        args = MagicMock()
        args.hosts = ['host1']
        args.approximate = False
        args.docker_command = ''
        args.script = 'test.sh'

        self._setup_sife_effect(output_mock)
        assert ('docker cp test.sh containerid1:/tmp && '
                'docker exec -it containerid1 chmod u+x /tmp/test.sh && '
                'docker exec -it containerid1 /tmp/test.sh && '
                'docker exec -it containerid1 bash') == \
            connections.DockerConnection.copy('containerid1', args)


@patch('scripts.connections.check_output_as_list')
class TestDockerComposeConnection:
    compose_containers = ['one', 'two']

    def _setup_sife_effect(self, output_mock):
        def side_effect(*args, **kwargs):
            if args[0] == 'docker-compose ps --filter="status=running" --services':
                return self.compose_containers
            if args[0] == 'docker-compose ps -q one':
                return ['containerid1']
            if args[0] == 'docker-compose ps -q two':
                return ['containerid2']
        output_mock.side_effect = side_effect

    def test_hosts_approximate(self, output_mock):
        args = MagicMock()
        args.hosts = ['ne']
        args.approximate = True

        self._setup_sife_effect(output_mock)
        assert ['containerid1'] == connections.DockerComposeConnection.hosts(args)

        args.hosts = ['o']
        assert ['containerid1', 'containerid2'] == connections.DockerComposeConnection.hosts(args)

        args.hosts = ['blah']
        with pytest.raises(ValueError):
            connections.DockerComposeConnection.hosts(args)

        args.hosts = ['ne', 'blah']
        assert ['containerid1'] == connections.DockerComposeConnection.hosts(args)


@patch('scripts.connections.check_output_as_list')
class TestSSHDockerConnection:
    host1_docker_containers = ['one,containerid1', 'two,containerid2']
    host2_docker_containers = ['one2,containerid12', 'two2,containerid22']

    def _setup_sife_effect(self, output_mock):
        def side_effect(*args, **kwargs):
            if args[0] == "ssh host1 docker ps --format '{{.Names}},{{.ID}}'":
                return self.host1_docker_containers
            if args[0] == "ssh host2 docker ps --format '{{.Names}},{{.ID}}'":
                return self.host2_docker_containers
        output_mock.side_effect = side_effect

    def test_no_hosts(self, output_mock):
        """ When there are no hosts, there is an error """
        with pytest.raises(ValueError):
            connections.SSHDockerConnection.hosts(MagicMock())

    def test_no_docker_containers(self, output_mock):
        """ When no args.docker_containers are passed, return all running containers """
        args = MagicMock()
        args.hosts = ['host1']
        self._setup_sife_effect(output_mock)

        hosts = connections.SSHDockerConnection.hosts(args)
        assert hosts == ['host1,containerid1', 'host1,containerid2']

        # Whene there are multiple hosts, all the docker containers are
        # returned:
        args.hosts = ['host1', 'host2']
        hosts = connections.SSHDockerConnection.hosts(args)
        assert hosts == [
            'host1,containerid1', 'host1,containerid2', '\n',
            'host2,containerid12', 'host2,containerid22']

    def test_hosts(self, output_mock):
        args = MagicMock()
        args.hosts = ['host1']
        args.docker_containers = 'one'
        args.approximate = False

        self._setup_sife_effect(output_mock)

        # If the hostname does match one, return it
        assert ['host1,containerid1'] == list(connections.SSHDockerConnection.hosts(args))

        # Multiple hosts, will show an error when both don't have the containers
        # listed
        args.hosts = ['host1', 'host2']
        args.docker_containers = 'one,two2'
        with pytest.raises(ValueError):
            connections.SSHDockerConnection.hosts(args)

        # Multiple hosts, will not show an error if using approximate matching.
        args.approximate = True
        hosts = connections.SSHDockerConnection.hosts(args)
        assert hosts == [
            'host1,containerid1', '\n',
            'host2,containerid12', 'host2,containerid22']

    def test_connect(self, output_mock):
        args = MagicMock()
        args.hosts = ['host1']
        args.docker_containers = 'one'
        args.approximate = False
        args.ssh_options = ''
        args.docker_command = ''

        self._setup_sife_effect(output_mock)
        assert 'ssh -t  host1 docker exec -it containerid1 bash' == \
            connections.SSHDockerConnection.connect('host1,containerid1', args)

    def test_command(self, output_mock):
        args = MagicMock()
        args.hosts = ['host1']
        args.docker_containers = 'one'
        args.approximate = False
        args.ssh_options = ''
        args.docker_command = ''
        args.command = 'pwd'

        self._setup_sife_effect(output_mock)
        assert 'ssh -t  host1 docker exec -it containerid1 pwd && ssh -t  host1 docker exec -it containerid1 bash' == \
            connections.SSHDockerConnection.command('host1,containerid1', args)

    def test_copy(self, output_mock):
        args = MagicMock()
        args.hosts = ['host1']
        args.docker_containers = 'one'
        args.approximate = False
        args.ssh_options = ''
        args.docker_command = ''
        args.script = 'test.sh'

        self._setup_sife_effect(output_mock)

        assert ('scp  test.sh host1:/tmp && ssh  host1 chmod u+x /tmp/test.sh && '
                'ssh -t  host1 docker cp /tmp/test.sh containerid1:/tmp && '
                'ssh -t  host1 docker exec -it containerid1 chmod u+x /tmp/test.sh && '
                'ssh -t  host1 docker exec -it containerid1 /tmp/test.sh && '
                'ssh -t  host1 docker exec -it containerid1 bash') == \
            connections.SSHDockerConnection.copy('host1,containerid1', args)

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

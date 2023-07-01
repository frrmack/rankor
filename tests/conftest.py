# Imports: pytest for fixtures, requests for sending test requests
import pytest
import requests

# Rankor imports: api server in a parallel thread for testing
from rankor.server import RankorServerThread


@pytest.fixture()
def server_ip():
    return '127.0.0.1'


@pytest.fixture()
def server_port():
    return '5000'


@pytest.fixture()
def api_url_scheme(server_ip, server_port):
    return f"http://{server_ip}:{server_port}"


@pytest.fixture()
def server(server_ip, server_port, api_url_scheme):
    # Start the server
    server = RankorServerThread(ip=server_ip, port=server_port)
    server.start()  
    assert server.is_alive()

    # Pre-cleanup before tests to ensure a fresh database: delete all data
    delete_all_things_endpoint = api_url_scheme + '/rankor/things/delete-all/'
    response = requests.delete(delete_all_things_endpoint)
    assert response.status_code == 200

    # Yield the server for the tests to come
    yield server

    # Clean up & tear down after the tests: delete all data again and
    # stop the server
    response = requests.delete(delete_all_things_endpoint)
    assert response.status_code == 200
    server.stop()
    assert not server.is_alive()




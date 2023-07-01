# Imports: pytest for fixtures, requests for sending test requests
import pytest
import requests


# Rankor imports: api server in a parallel thread for testing
from rankor.server import RankorServerThread

# Configuration imports
import settings



# Test data fixtures
@pytest.fixture(scope="function")
def movie_data():
    return [
        {"name": "Alien",
        "image_url": "https://m.media-amazon.com/images/I/81TpGaKY3ML._AC_UY436_QL65_.jpg",
        "other_data": {"director":"James Cameron", "year":1979},
        },
        {"name": "The Terminator",
        "image_url": "https://m.media-amazon.com/images/I/61qCgQZyhOL._AC_SY879_.jpg",
        "other_data": {"director":"James Cameron", "year":1982},
        },
        {"name": "Aliens",
        "image_url": "https://m.media-amazon.com/images/I/91kkGWtyqTL._AC_SL1500_.jpg",
        "other_data": {"director":"James Cameron", "year":1986},
        },
        {"name": "The Abyss",
        "image_url": "https://m.media-amazon.com/images/I/81o0AjxXeyL._AC_UY436_QL65_.jpg",
        "other_data": {"director":"James Cameron", "year":1989},
        },
        {"name": "Terminator 2: The Judgement Day",
        "image_url": "https://m.media-amazon.com/images/I/81rFodFkebL._AC_UY436_QL65_.jpg",
        "other_data": {"director":"James Cameron", "year":1991},
        },
        {"name": "True Lies",
        "image_url": "https://m.media-amazon.com/images/I/81rFodFkebL._AC_UY436_QL65_.jpg",
        "other_data": {"director":"James Cameron", "year":1994},
        },
        {"name": "Titanic",
        "image_url": "https://m.media-amazon.com/images/I/81rFodFkebL._AC_UY436_QL65_.jpg",
        "other_data": {"director":"James Cameron", "year":1997},
        },
    ]



# Test server setup fixtures
@pytest.fixture(scope="session")
def server_ip():
    return '127.0.0.1'


@pytest.fixture(scope="session")
def server_port():
    return '5000'


@pytest.fixture(scope="session")
def api_url_scheme(server_ip, server_port):
    return f"http://{server_ip}:{server_port}"


@pytest.fixture(scope="function")
def server(server_ip, server_port, api_url_scheme):
    """ 
    Run an api development server in a parallel thread so that tests can send
    requests to it and evaluate the responses.

    This fixture is function scoped. It's requested by each test separately.
    This means that each test will start up with a fresh server instance and
    tear it down at the end, rather than all tests sharing one server instance.
    This is cleaner and ensures statelessness.
    """
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



# Endpoint fixtures
@pytest.fixture()
def things_endpoint(api_url_scheme):
    return api_url_scheme + '/rankor/things/'

@pytest.fixture(autouse=True)
def delete_all_things_endpoint(api_url_scheme):
    return api_url_scheme + '/rankor/things/delete-all'



# Config fixtures
@pytest.fixture()
def things_page_size():
    return settings.NUMBER_ITEMS_IN_EACH_PAGE["thing"]
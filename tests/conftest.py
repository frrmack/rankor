# Python standard library imports: pytest for fixtures, urljoin for building url
# paths
import pytest
from urllib.parse import urljoin

# Third party imports: requests for interfacing with the api server
import requests

# Rankor imports: app factory to create a custom testing app, api server in a
# parallel thread for testing 
from rankor import create_app as create_rankor_app
from rankor.server import RankorServerThread

# Rankor configuration imports
from rankor.config import RANKOR_CONFIG


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


@pytest.fixture(scope="session")
def testing_database_name():
    return "_rankor_testing_db"


@pytest.fixture(scope="session")
def mongo_testing_database_uri(testing_database_name):
    return "".join(
        [
            RANKOR_CONFIG['database']['mongo_server_uri'],
            testing_database_name
        ]
    )



# Endpoint fixtures
@pytest.fixture(scope="session")
def things_endpoint(api_url_scheme):
    return urljoin(api_url_scheme, '/rankor/things/')

@pytest.fixture(scope="session")
def delete_all_things_endpoint(api_url_scheme):
    return urljoin(api_url_scheme, '/rankor/things/delete-all/')



# Config fixtures
@pytest.fixture(scope="function")
def things_page_size():
    return RANKOR_CONFIG['pagination']['thing']['page_size']



# Rankor testing server fixture
@pytest.fixture(scope="function")
def server(server_ip, 
           server_port, 
           delete_all_things_endpoint, 
           mongo_testing_database_uri):
    """ 
    Run an api development server in a parallel thread so that tests can send
    requests to it and evaluate the responses.

    This fixture is function scoped. It's requested by each test separately.
    This means that each test will start up with a fresh server instance and
    tear it down at the end, rather than all tests sharing one server instance.
    This is cleaner and ensures statelessness.
    """
    # Initialize testing app
    test_app = create_rankor_app(mongo_uri=mongo_testing_database_uri)

    # Start the server
    server = RankorServerThread(ip=server_ip, port=server_port, app=test_app)
    server.start()  
    assert server.is_alive()

    # Pre-cleanup before tests to ensure a fresh database: delete all data
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




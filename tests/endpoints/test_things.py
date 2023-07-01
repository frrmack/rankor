import pytest
import requests

class TestThingsEndpoint:

    # The following endpoint fixtures are used by all the tests of this class.
    # Note that the server fixture is not class or session scoped, but
    # function scoped. It's requested by each test separately. This means
    # each test will start up with a fresh server instance and tear it down
    # at the end, rather than all tests sharing one server instance. This is
    # cleaner and ensures statelessness.
    @pytest.fixture(scope="class")
    def things_endpoint(self, api_url_scheme):
        return api_url_scheme + '/rankor/things/'
    
    @pytest.fixture(scope="class")
    def delete_all_things_endpoint(self, api_url_scheme):
        return api_url_scheme + '/rankor/things/delete-all'

    def test_list_all_things_response(self, server, things_endpoint):
        response = requests.get(things_endpoint)
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["http_status_code"] == 200
        assert response_data["result"] == "success"
        assert response_data["things"] == []
        assert response_data["msg"] == ("Successfully retrieved page 1 of 1 "
                                        "for the list of all 0 things")
        assert response_data["_page"] == 1
        assert response_data["_num_things_in_page"] == 0
        assert response_data["_links"]["last_page"]["page"] == 1
        assert response_data["_links"]["last_page"]["href"] == \
                                                    f"{things_endpoint}?page=1"
        assert response_data["_links"]["this_page"]["page"] == 1
        assert response_data["_links"]["this_page"]["href"] == \
                                                    f"{things_endpoint}?page=1"


    def test_create_a_thing(self, server, things_endpoint, movie_data):
        pass


    def test_delete_all_things(self, server, delete_all_things_endpoint):
        response = requests.delete(delete_all_things_endpoint)
        assert response.status_code == 200
        assert response.json() == {"http_status_code": 200,
                                   "msg": "0 things deleted",
                                   "result": "success"}

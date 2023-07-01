import requests


def test_list_all_things_response(server, things_endpoint):
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



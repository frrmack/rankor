from urllib.parse import urljoin

import requests


def test_get_a_thing(server, things_endpoint, movie_data):
    # insert a single thing to then retrieve
    single_movie = movie_data[0]
    response = requests.post(things_endpoint, json=single_movie)
    assert response.status_code == 200
    movie_id = response.json()["thing"]["id"]
    time_created = response.json()["thing"]["time_created"]
    # now get it back
    endpoint = urljoin(things_endpoint, movie_id,'/')
    response = requests.get(endpoint)
    response_data = response.json()
    assert response_data["http_status_code"] == 200
    assert response_data["result"] == "success"
    assert response_data["thing"]["name"] == single_movie['name']
    assert response_data["thing"]["image_url"] == single_movie['image_url']
    assert response_data["thing"]["other_data"] == single_movie['other_data']
    thing_id = response_data["thing"]["id"]
    assert response_data["msg"] == (f"Successfully retrieved thing "
                                    f"with id {thing_id}")
    assert response_data["thing"]["time_created"] == time_created


def test_get_a_thing_missing_error(server, things_endpoint):
    # try to retrieve a thing that doesn't exist, it should fail
    non_existing_id = "64ab5f14c8757d1f89bb4bf0"
    endpoint = urljoin(things_endpoint, non_existing_id, '/')
    response = requests.get(endpoint)
    response_data = response.json()
    assert response_data["http_status_code"] == 404
    assert response_data["result"] == "failure"
    assert response_data["error_type"] == "ResourceNotFoundInDatabaseError"
    assert response_data["error_category"] == "HTTP error"
    assert response_data["error"] == (f"The requested thing with the id "
                                        f"{non_existing_id} was not found "
                                        f"in the database. Please check the "
                                        f"requested data carefully and try "
                                        f"again.")


def test_get_a_thing_non_ObjectId_404_error(server, things_endpoint):
    # try to retrieve a thing with an id that's not a valid ObjectId
    # this should not match existing url rules and result in a 404
    non_ObjectId_id= "42"
    endpoint = urljoin(things_endpoint, non_ObjectId_id, '/')
    response = requests.get(endpoint)
    response_data = response.json()
    assert response_data["http_status_code"] == 404
    assert response_data["result"] == "failure"
    assert response_data["error_type"] == "NotFound"
    assert response_data["error_category"] == "HTTP error"
    assert response_data["error"] == ("The requested URL was not found on "
                                        "the server. If you entered the URL "
                                        "manually please check your spelling "
                                        "and try again.")

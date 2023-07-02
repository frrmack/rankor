import json
from urllib.parse import urljoin

import requests


def test_create_a_thing(server, things_endpoint, movie_data):
    single_movie = single_movie_data_dict = movie_data[0]
    response = requests.post(things_endpoint, json=single_movie_data_dict)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["http_status_code"] == 200
    assert response_data["result"] == "success"
    assert response_data["thing"]["name"] == single_movie['name']
    assert response_data["thing"]["image_url"] == single_movie['image_url']
    assert response_data["thing"]["other_data"] == single_movie['other_data']
    thing_id = response_data["thing"]["id"]
    time_created = response_data["thing"]["time_created"]
    assert response_data["msg"] == f"New thing created and given id {thing_id}"
    # make sure it's there
    endpoint = urljoin(things_endpoint, thing_id, '/')
    response = requests.get(endpoint)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["http_status_code"] == 200
    assert response_data["result"] == "success"
    assert response_data["thing"]["name"] == single_movie['name']
    assert response_data["thing"]["other_data"] == single_movie['other_data']
    assert response_data["thing"]["id"] == thing_id
    assert response_data["thing"]["time_created"] == time_created



def test_create_a_thing_format_header_error(server, 
                                            things_endpoint, 
                                            movie_data):
    single_movie_data_json = json.dumps(movie_data[0])
    response = requests.post(things_endpoint, data=single_movie_data_json)
    # Note that we used the "data" keyword argument and not the "json" kwarg
    # with the requests' post method, the request won't have the json
    # content-type header and therefore this should fail
    response_data = response.json()
    assert response.status_code == 415
    assert response_data["http_status_code"] == 415
    assert response_data["result"] == "failure"
    assert response_data["error_type"] == "UnsupportedMediaType"
    assert response_data["error_category"] == "HTTP error"
    assert response_data["error"] == ("Did not attempt to load JSON data "
                                        "because the request Content-Type "
                                        "was not 'application/json'.")


def test_create_a_thing_data_type_error(server, 
                                        things_endpoint, 
                                        movie_data):
    single_movie_data_dict = movie_data[0]
    single_movie_data_dict["image_url"] = "An image with a black alien"
    # Note that the string we are using for the image_url field is not a url
    # This should fail the type validation
    response = requests.post(things_endpoint, json=single_movie_data_dict)
    response_data = response.json()
    assert response.status_code == 400
    assert response_data["http_status_code"] == 400
    assert response_data["result"] == "failure"
    assert response_data["error_type"] == "ValidationError"
    assert response_data["error_category"] == "Data validation error"
    assert response_data["error_details"]["number_of_validation_errors"] == 1
    assert {'loc': ['image_url'], 
            'msg': 'invalid or missing URL scheme', 
            'type': 'value_error.url.scheme'
            } in response_data["error_details"]["validation_error_list"]         
    assert response_data["error"] == ("The data of this resource does not "
                                        "fully match the validation "
                                        "requirements. Please ensure "
                                        "existence of all required fields, "
                                        "valid field names, and valid data "
                                        "types for those fields' values.")


def test_create_a_thing_multiple_data_type_errors(server, 
                                                  things_endpoint, 
                                                  movie_data):
    single_movie_data_dict = movie_data[0]
    single_movie_data_dict["image_url"] = "An image with a black alien"
    single_movie_data_dict["other_data"] = "The director is James Cameron"
    # Note that now we have two wrong data types in this Thing candidate:
    # A string for the "image_url" field that's not a url (should be a url),
    # and a string for the "other_data" field (should be a dict)
    # This also should fail the type validation (twice)
    response = requests.post(things_endpoint, json=single_movie_data_dict)
    response_data = response.json()
    assert response.status_code == 400
    assert response_data["http_status_code"] == 400
    assert response_data["result"] == "failure"
    assert response_data["error_type"] == "ValidationError"
    assert response_data["error_category"] == "Data validation error"
    assert response_data["error_details"]["number_of_validation_errors"] == 2
    assert {'loc': ['image_url'], 
            'msg': 'invalid or missing URL scheme', 
            'type': 'value_error.url.scheme'
            } in response_data["error_details"]["validation_error_list"]
    assert {'loc': ['other_data'], 
            'msg': 'value is not a valid dict', 
            'type': 'type_error.dict'
            } in response_data["error_details"]["validation_error_list"]
    assert response_data["error"] == ("The data of this resource does not "
                                        "fully match the validation "
                                        "requirements. Please ensure "
                                        "existence of all required fields, "
                                        "valid field names, and valid data "
                                        "types for those fields' values.")


def test_create_a_thing_missing_field_error(server, 
                                            things_endpoint, 
                                            movie_data):
    single_movie_data_dict = movie_data[0]
    single_movie_data_dict.pop("name")
    # Note that we removed the required field "name"
    # This should fail the type validation
    response = requests.post(things_endpoint, json=single_movie_data_dict)
    response_data = response.json()
    assert response.status_code == 400
    assert response_data["http_status_code"] == 400
    assert response_data["result"] == "failure"
    assert response_data["error_type"] == "ValidationError"
    assert response_data["error_category"] == "Data validation error"
    assert response_data["error_details"]["number_of_validation_errors"] == 1
    assert {'loc': ['name'], 
            'msg': 'field required', 
            'type': 'value_error.missing'
            } in response_data["error_details"]["validation_error_list"]         
    assert response_data["error"] == ("The data of this resource does not "
                                        "fully match the validation "
                                        "requirements. Please ensure "
                                        "existence of all required fields, "
                                        "valid field names, and valid data "
                                        "types for those fields' values.")


def test_create_a_duplicate_thing_error(server, 
                                        things_endpoint, 
                                        movie_data):
    # insert a single movie
    single_movie = movie_data[0]
    response = requests.post(things_endpoint, json=single_movie)
    assert response.status_code == 200
    movie_id = response.json()["thing"]["id"]
    # now try to insert it (with the same name) a second time: it should fail
    response = requests.post(things_endpoint, json=single_movie)
    assert response.status_code == 409
    def ensure_correct_failure_response(response_data):
        assert response_data["http_status_code"] == 409
        assert response_data["result"] == "failure"
        assert response_data["error_type"] == "SameNameResourceAlreadyExistsError"
        assert response_data["error_category"] == "HTTP error"
        assert response_data["error"] == ("A thing with the same name already "
                                        "exists in the database. Either update "
                                        "that thing instead, or delete that "
                                        "before creating this, or give this "
                                        "new thing a different name")
        assert response_data["existing_resource"]["id"] == movie_id
    ensure_correct_failure_response(response.json())
    # now try to insert a new Thing that's not the same but has the same name
    new_movie_same_name = {
            "name":single_movie["name"], 
            "category":"Box Office Busts"
    }
    response = requests.post(things_endpoint, json=new_movie_same_name)
    assert response.status_code == 409
    ensure_correct_failure_response(response.json())
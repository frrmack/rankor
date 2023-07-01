import pytest
import requests
from rankor.json import to_json



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


    def test_create_a_thing(self, server, things_endpoint, movie_data):
        single_movie = single_movie_data_dict = movie_data[0]
        response = requests.post(things_endpoint, json=single_movie_data_dict)
        response_data = response.json()
        assert response.status_code == 200
        assert response_data["http_status_code"] == 200
        assert response_data["result"] == "success"
        assert response_data["thing"]["name"] == single_movie['name']
        assert response_data["thing"]["image_url"] == single_movie['image_url']
        assert response_data["thing"]["other_data"] == single_movie['other_data']
        thing_id = response_data["thing"]["id"]
        assert response_data["msg"] == f"New thing created and given id {thing_id}"
        assert "time_created" in response_data["thing"]


    def test_create_a_thing_format_header_error(self, 
                                                server, 
                                                things_endpoint, 
                                                movie_data):
        single_movie_data_json = to_json(movie_data[0])
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


    def test_create_a_thing_data_type_error(self, 
                                            server, 
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


    def test_create_a_thing_multiple_data_type_errors(self, 
                                                     server, 
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


    def test_create_a_thing_missing_field_error(self, 
                                                server, 
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


    def test_get_a_thing(self, server, things_endpoint, movie_data):
        # insert a single thing to then retrieve
        single_movie = movie_data[0]
        response = requests.post(things_endpoint, json=single_movie)
        assert response.status_code == 200
        print(response.json())
        movie_id = response.json()["thing"]["id"]
        time_created = response.json()["thing"]["time_created"]
        # not get it back
        endpoint = f"{things_endpoint}{movie_id}"
        response = requests.get(endpoint)
        response_data = response.json()
        print(response_data)
        assert response_data["http_status_code"] == 200
        assert response_data["result"] == "success"
        assert response_data["thing"]["name"] == single_movie['name']
        assert response_data["thing"]["image_url"] == single_movie['image_url']
        assert response_data["thing"]["other_data"] == single_movie['other_data']
        thing_id = response_data["thing"]["id"]
        assert response_data["msg"] == f"Successfully retrieved thing with id {thing_id}"
        assert response_data["thing"]["time_created"] == time_created
        assert False


    def test_edit_a_thing(self, server, things_endpoint, movie_data):
        # insert a movie (to then edit)
        single_movie = movie_data[0]
        response = requests.post(things_endpoint, json=single_movie)
        assert response.status_code == 200
        movie_id = response.json()["thing"]["id"]
        # now we want to change the name, add a category field, and overwrite
        # the other_data field with new info (but keep the image_url same)
        endpoint = f"{things_endpoint}{movie_id}/"
        changes = {
            "name": "Alien 3",
            "category": "Science Fiction Movies",
            "other_data": {
                "director": "David Fincher", 
                "studio": "20th Century Fox",
            }
        }
        response = requests.put(endpoint, json=changes)
        response_data = response.json()
        assert response.status_code == 200
        assert response_data["http_status_code"] == 200
        assert response_data["result"] == "success"
        assert response_data["msg"] == f"Successfully edited thing with id {movie_id}"
        assert response_data["thing"]["name"] == changes["name"]
        assert response_data["thing"]["category"] == changes["category"]
        assert response_data["thing"]["other_data"] == changes["other_data"]
        assert response_data["thing"]["id"] == movie_id
        if "image_url" in single_movie:
            assert response_data["thing"]["image_url"] == single_movie["image_url"]
        if "other_data" in single_movie and "year" in single_movie["other_data"]:
            assert "year" not in response_data["thing"]["other_data"]
        assert "time_created" in response_data["thing"]
        assert "time_edited" in response_data["thing"]


    def test_delete_a_thing(self, server, things_endpoint, movie_data):
        # insert a movie (to then delete)
        single_movie = movie_data[0]
        response = requests.post(things_endpoint, json=single_movie)
        assert response.status_code == 200
        movie_id = response.json()["thing"]["id"]
        time_created = response.json()["thing"]["time_created"]
        # now delete it
        endpoint = f"{things_endpoint}{movie_id}"
        response = requests.delete(endpoint)
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["http_status_code"] == 200
        assert response_data["result"] == "success"
        assert response_data["msg"] == f"thing with id {movie_id} deleted."
        assert response_data["thing"].pop("id") == movie_id
        assert response_data["thing"].pop("time_created") == time_created
        assert response_data["thing"] == single_movie

    


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
 
 

    def test_delete_all_things(self, server, delete_all_things_endpoint):
        response = requests.delete(delete_all_things_endpoint)
        assert response.status_code == 200
        assert response.json() == {"http_status_code": 200,
                                   "msg": "0 things deleted",
                                   "result": "success"}

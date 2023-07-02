from urllib.parse import urljoin

import requests

from rankor.utils import append_or_update_batch_number


def test_delete_a_thing(server, 
                        things_endpoint, 
                        movie_data):
    # insert a movie (to then delete)
    single_movie = movie_data[0]
    response = requests.post(things_endpoint, json=single_movie)
    assert response.status_code == 200
    movie_id = response.json()["thing"]["id"]
    time_created = response.json()["thing"]["time_created"]
    # now delete it
    endpoint = urljoin(things_endpoint, movie_id)
    response = requests.delete(endpoint)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["http_status_code"] == 200
    assert response_data["result"] == "success"
    assert response_data["msg"] == f"thing with id {movie_id} deleted."
    assert response_data["thing"].pop("id") == movie_id
    assert response_data["thing"].pop("time_created") == time_created
    assert response_data["thing"] == single_movie
    # make sure it's not in there anymore
    response = requests.get(endpoint)
    assert response.status_code == 404
    print(response.json())
    assert response.json()["error_type"] == "ResourceNotFoundInDatabaseError"


def test_delete_all_things(server, 
                           delete_all_things_endpoint):
    response = requests.delete(delete_all_things_endpoint)
    assert response.status_code == 200
    assert response.json() == {
                                "http_status_code": 200,
                                "msg": "0 things deleted",
                                "result": "success"
                              }


def test_insert_many_things_then_delete_all(server, 
                                            things_endpoint, 
                                            delete_all_things_endpoint,
                                            things_page_size,
                                            movie_data):
    # Insert all movies from the test data repeatedly (20 times each) to get a
    # large number of Things in there. Change the name in each batch to avoid a
    # HTTP 409 SameNameResourceAlreadyExistsError from trying to create a Thing
    # with a duplicate name
    for batch_no in range(20):
        for movie_dict in movie_data:
            movie_dict["name"] = append_or_update_batch_number(
                movie_dict["name"],
                batch_no
            )
            response = requests.post(things_endpoint, json=movie_dict)
            assert response.status_code == 200
    num_movies = len(movie_data) * 20
    num_pages = num_movies//things_page_size+1
    first_page_size = min(num_movies, things_page_size)
    # make sure that they are all in there
    response = requests.get(things_endpoint)
    assert response.status_code == 200
    assert response.json()["_links"]["last_page"]["page"] == num_pages
    assert len(response.json()["things"]) == first_page_size
    # now delete all of them
    response = requests.delete(delete_all_things_endpoint)
    assert response.status_code == 200
    assert response.json() == {
                                "http_status_code": 200,
                                "msg": f"{num_movies} things deleted",
                                "result": "success"
                              }
    # make sure that there are none left
    response = requests.get(things_endpoint)
    assert response.status_code == 200
    assert response.json()["_links"]["last_page"]["page"] == 1
    assert len(response.json()["things"]) == 0
    

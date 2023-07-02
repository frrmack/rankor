import requests

from rankor.utils import append_or_update_batch_number


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


def test_insert_and_list_many_things(server, things_endpoint, movie_data):
    # insert all movies from the test data
    for movie_dict in movie_data:
        response = requests.post(things_endpoint, json=movie_dict)
        assert response.status_code == 200
    num_movies = len(movie_data)
    # now list all of them
    response = requests.get(things_endpoint)
    response_data = response.json()
    assert response_data["http_status_code"] == 200
    assert response_data["result"] == "success"
    assert response_data["msg"] == (f"Successfully retrieved page 1 of 1 "
                                    f"for the list of all {num_movies} things")
    assert response_data["_page"] == 1
    assert response_data["_num_things_in_page"] == num_movies
    assert response_data["_links"]["last_page"]["page"] == 1
    assert response_data["_links"]["last_page"]["href"] == \
                                                f"{things_endpoint}?page=1"
    assert response_data["_links"]["this_page"]["page"] == 1
    assert response_data["_links"]["this_page"]["href"] == \
                                                f"{things_endpoint}?page=1"
    for thing in response_data["things"]:
        # remove added rankor data not found in original test data
        thing.pop("id")
        thing.pop("time_created")
        # make sure the data was in the original test dataset
        assert thing in movie_data


def test_listing_with_pagination(server, 
                                 things_endpoint, 
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
    # now list all of them, ensure we get the proper first page
    response = requests.get(things_endpoint)
    response_data = response.json()
    def ensure_proper_response(response_data, page):
        assert response_data["http_status_code"] == 200
        assert response_data["result"] == "success"
        assert response_data["msg"] == (f"Successfully retrieved page {page} "
                                        f"of {num_pages} for the "
                                        f"list of all {num_movies} things")
        assert response_data["_page"] == page
        assert response_data["_links"]["last_page"]["page"] == num_pages
    ensure_proper_response(response.json(), page=1)
    assert response_data["_num_things_in_page"] == first_page_size
    # flip through all pages, make sure everything is in order
    last_page = response_data["_links"]["last_page"]["page"]
    while response_data["_page"] != last_page:
        next_page_url = response_data["_links"]["next_page"]["href"]
        next_page = response_data["_links"]["next_page"]["page"]
        response = requests.get(next_page_url)
        response_data = response.json()
        ensure_proper_response(response_data, page=next_page)
        # last page should not have a next_page link in response_data["_links"]
        if "next_page" in response_data["_links"]:
            assert response_data["_num_things_in_page"] == things_page_size
            assert len(response_data["things"]) == things_page_size
        else:
            last_page_size = num_movies % things_page_size
            assert response_data["_num_things_in_page"] == last_page_size
            assert len(response_data["things"]) == last_page_size



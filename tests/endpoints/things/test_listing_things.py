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
    # insert all movies from the test data repeatedly (10 times each)
    # to get a large number of Things in there
    for i in range(10):
        for movie_dict in movie_data:
            # change movie name in each batch to avoid
            # SameNameResourceAlreadyExistsError from trying to create a Thing
            # with a duplicate name
            movie_dict["name"] = (
                movie_dict["name"].rsplit(" --- batch",1)[0]
                + f" --- batch {i}"
            )
            response = requests.post(things_endpoint, json=movie_dict)
            assert response.status_code == 200
    num_movies = len(movie_data) * 10
    num_pages = num_movies//things_page_size+1
    # now list all of them
    response = requests.get(things_endpoint)
    response_data = response.json()
    assert response_data["http_status_code"] == 200
    assert response_data["result"] == "success"
    assert response_data["msg"] == (f"Successfully retrieved page 1 of {num_pages} "
                                    f"for the list of all {num_movies} things")
    assert response_data["_page"] == 1
    assert response_data["_num_things_in_page"] == things_page_size
    assert response_data["_links"]["last_page"]["page"] == num_pages
    # flip through all pages, make sure everything is in order
    while response_data["_page"] != response_data["_links"]["last_page"]["page"]:
        next_page_url = response_data["_links"]["next_page"]["href"]
        next_page = response_data["_links"]["next_page"]["page"]
        response = requests.get(next_page_url)
        response_data = response.json()
        assert response_data["http_status_code"] == 200
        assert response_data["result"] == "success"
        assert response_data["msg"] == (f"Successfully retrieved page {next_page} of {num_pages} "
                                        f"for the list of all {num_movies} things")
        assert response_data["_page"] == next_page
        if "next_page" in response_data["_links"]:
            assert response_data["_num_things_in_page"] == things_page_size
            assert len(response_data["things"]) == things_page_size
        else:
            assert response_data["_num_things_in_page"] == num_movies % things_page_size
            assert len(response_data["things"]) == num_movies % things_page_size



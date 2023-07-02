from urllib.parse import urljoin

import requests


def test_edit_a_thing(server, things_endpoint, movie_data):
    # insert a movie (to then edit)
    single_movie = movie_data[0]
    response = requests.post(things_endpoint, json=single_movie)
    assert response.status_code == 200
    movie_id = response.json()["thing"]["id"]
    # now we want to change the name, add a category field, and overwrite
    # the other_data field with new info (but keep the image_url same)
    endpoint = urljoin(things_endpoint, movie_id)
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

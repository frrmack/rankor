import requests


def test_delete_a_thing(server, things_endpoint, movie_data):
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



def test_delete_all_things(server, delete_all_things_endpoint):
    response = requests.delete(delete_all_things_endpoint)
    assert response.status_code == 200
    assert response.json() == {"http_status_code": 200,
                                "msg": "0 things deleted",
                                "result": "success"}

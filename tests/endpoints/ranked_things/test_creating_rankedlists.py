import requests

def test_create_a_ranked_list(server, ranked_lists_endpoint, movie_data):
    list_name = "James Cameron Movies"
    new_ranked_list_data_dict = {"name": list_name}
    response = requests.post(ranked_lists_endpoint, json=new_ranked_list_data_dict)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["http_status_code"] == 200
    assert response_data['ranked_list']['data']['name'] == list_name
    assert isinstance(response_data['ranked_list']['data']['id'], str)


 
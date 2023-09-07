from urllib.parse import urljoin
import requests

def test_retrieve_a_ranked_list(server, ranked_lists_endpoint, movie_data):
    # create a ranked list
    list_name = "James Cameron Movies"
    new_ranked_list_data_dict = {"name": list_name}
    response = requests.post(ranked_lists_endpoint, json=new_ranked_list_data_dict)
    assert response.status_code == 200
    response_data = response.json()
    ranked_list_id_str = response_data['ranked_list']['data']['id']
    # now get it back
    endpoint = urljoin(ranked_lists_endpoint, ranked_list_id_str,'/')
    response = requests.get(endpoint)
    response_data = response.json()
    assert response_data["http_status_code"] == 200
    assert response_data["result"] == "success"
    assert response_data["ranked_list"]["data"]["name"] == list_name
    assert response_data["ranked_list"]["data"]["id"] == ranked_list_id_str

 
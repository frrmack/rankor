import requests

def test_delete_all_things(server, api_url_scheme):
    endpoint = api_url_scheme + '/rankor/things/delete-all'
    response = requests.delete(endpoint)
    assert response.status_code == 200
    assert response.json() == {"http_status_code": 200,
                               "msg": "0 things deleted",
                               "result": "success"}

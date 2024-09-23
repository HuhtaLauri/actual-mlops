import unittest
from unittest.mock import patch
import requests
from src.engineering.github.collector import (
    get_api_data,
    construct_api_url
)

class TestGithubApi(unittest.TestCase):

    def test_can_call_api(self):
        resp = requests.get("https://api.github.com")
        print(resp.status_code)
        assert resp.status_code == 200

    def test_commits_response_structure(self):
        url = construct_api_url("repos", "apache", "kafka", "commits")

        params = {
            "per_page": 1
        }

        resp = get_api_data(url, params)
        
        resp_keys = resp.json()[0].keys()

        assert "sha" in resp_keys
        assert "node_id" in resp_keys
        assert "commit" in resp_keys
        assert "author" in resp_keys
        assert "committer" in resp_keys
        assert "parents" in resp_keys


if __name__ == "__main__":
    unittest.main()

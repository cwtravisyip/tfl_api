"Unit test for functions in the tfl_api submodule"

import os
from parameterized import parameterized
import logging
import requests
from tenacity import RetryError
import unittest
from unittest.mock import patch, Mock

from src.tfl_api import get_headers_from_env, validate_headers, TflApiClient

logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


@unittest.skip("Skipping tests since testing Client Instantiation Cover these test.")
class TestHeaderFromEnv(unittest.TestCase):

    @patch.dict(os.environ, {}, clear=True)
    def test_env_header_empty(self):
        """Test that an EnvironmentError is raised if TFL_ACCESS_KEY is not set."""

        with self.assertRaises(EnvironmentError):
            get_headers_from_env()

    @patch.dict(os.environ, {"TFL_ACCESS_KEY": "LoremIpsum"}, clear=True)
    def test_env_header(self):
        headers = get_headers_from_env()
        self.assertEqual(headers, {"app_key": "LoremIpsum", "content-type": "application/json"})

class TestValidateHeaders(unittest.TestCase):

    def test_valid_header(self):
        """Test valid headers pass validation."""

        headers = {"app_key": "LoremIpsum", "content-type": "application/json"}
        with self.assertLogs('src.tfl_api', level='INFO') as cm:
            validate_headers(headers)
            self.assertIn("Headers is valid for access to TFL API.", cm.output[0])

    @parameterized.expand(["HEADERS is str", ["HEADERS is list"]])
    def test_invalid_type_header_type(self, headers):
        """Test invalid header types raise TypeError."""

        with self.assertRaises(TypeError):
            validate_headers(headers)
  
    @parameterized.expand([
        ({"app_key":"HEADERS MISSING CONTENT TYPE"},),
        ({"app_key":b"NOT STR APP K","content-type":"application/json"},),
    ])
    def test_invalid_value_header_type(self, headers):
        """Test invalid header values raise ValueError."""

        with self.assertRaises(ValueError):
            validate_headers(headers)


class TestApiClientInstantiation(unittest.TestCase):
    
    @patch.dict(os.environ, {"TFL_ACCESS_KEY": "LoremIpsum"}, clear=True)
    def test_client_init_no_headers(self):
        """Test that the TflApiClient can be instantiated with environment variable."""

        client = TflApiClient()
        self.assertEqual(client.headers, {"app_key": "LoremIpsum", "content-type": "application/json"})

    def test_client_init_with_headers(self):
        """Test that the TflApiClient can be instantiated with custom headers."""

        headers = {"app_key": "CustomKey", "content-type": "application/json"}
        client = TflApiClient(headers=headers)
        self.assertEqual(client.headers, headers)

    @patch.dict(os.environ, {}, clear=True)
    def test_env_header_empty(self):
        """Test that an EnvironmentError is raised if TFL_ACCESS_KEY is not set."""

        with self.assertRaises(EnvironmentError):
            client = TflApiClient()

class TestRequestEndpoint(unittest.TestCase):

    def setUp(self):
        self.client = TflApiClient(headers={"app_key": "LoremIpsum", "content-type": "application/json"})

    def tearnDown(self):
        pass
    
    def test_request_endpoint_success(self):
        """Test that the request_endpoint method returns a response on success."""

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        with patch('src.tfl_api.requests.get', return_value=mock_response):
            res = self.client.request_endpoint('http://test')
            assert res == mock_response

    def test_request_endpoint_http_error(self):
        """Test that the request_endpoint method retries on HTTPError.
        
        Expect if the request keeps failing, a RetryError is raised from the tenacity retry decorator.
        """

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("Bad Request")
        with patch('src.tfl_api.requests.get', return_value=mock_response):
            with self.assertRaises(RetryError):
                self.client.request_endpoint('http://test')

    def test_request_endpoint_2XX(self):
        """Test that a warning is logged for non-200 2XX status codes."""

        mock_response = Mock()
        mock_response.status_code = 201
        with patch('src.tfl_api.requests.get', return_value=mock_response):
            with self.assertLogs("src.tfl_api", level="WARNING") as cm:
                self.client.request_endpoint('http://test')
                self.assertIn("Request to http://test returned status code 201", cm.output[0])
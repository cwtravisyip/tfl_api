import io
import logging
import os
from functools import lru_cache
from typing import Dict, List, Literal, Optional, Union

import requests
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


class TflApiClient:
    """Custom client for TFL API."""
    
    def __init__(self, headers: Union[Dict, None] = None):
        
        if headers is None:
            LOGGER.debug("No headers provided. Attempting to get headers from environment variables.")
            self.headers = get_headers_from_env()
        else:
            validate_headers(headers)
            self.headers = headers

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(requests.RequestException),
    )
    def request_endpoint(self, endpoint: str) -> requests.Response:

        LOGGER.debug(f"Requesting line IDs from endpoint: {endpoint}")
        res = requests.get(endpoint, headers=self.headers)
        try:
        res.raise_for_status()
        except requests.RequestException as e:
            LOGGER.error(f"Request to {endpoint} failed: {e}")
            LOGGER.debug(f"Response content: {res.content}")

            raise

        if res.status_code != 200:
            LOGGER.warning(f"Request to {endpoint} returned status code {res.status_code}")

        return res

    @lru_cache(maxsize=3)
    def get_line_ids(self, service_types: Optional[Literal["Regular", "Night"]] = "Regular") -> List[str]:

        endpoint = f"https://api.tfl.gov.uk/Line/Route?{service_types}"
        res = self.request_endpoint(endpoint)

        # return only the service name, service id, and service mode. Additional data available from res.json()
        # return [[service["modeName"], service["id"], service["name"]] for service in res.json()]
        # instead of returning the processed data, preserve the response object
        return res.json()


def get_headers_from_env() -> Dict:
    if os.getenv("TFL_ACCESS_KEY") is None:
        raise EnvironmentError("Environment variable `TFL_ACCESS_KEY` is not set.")
    else:
        LOGGER.debug("Successfully retrieved TFL_ACCESS_KEY from environment variables.")
        return {"app_key": os.getenv("TFL_ACCESS_KEY"), "content-type": "application/json"}


def validate_headers(headers: dict):
    """Validate the headers for TFL API access.
    
    The header must be a dictionary with the following key-value pairs:
        - "app_key": str
        - "content-type": "application/json"
    Raises:
        TypeError: If headers is not a dictionary.
        ValueError: If headers is missing required key-value pairs or if the value of "app
    """

    if not isinstance(headers, dict):
        raise TypeError(f"Header must be type dict. Got type {type(headers)}")
    if len(set(["app_key", "content-type"]).difference(headers)) > 0:
        raise ValueError(f"Headers missing key-value pair(s): {set(['app_key','content-type']).difference(headers)}")

    if not isinstance(headers["app_key"], str):
        raise ValueError("The `app_key` value in the headers is not string type.")
    else:
        LOGGER.debug("Headers is valid for access to TFL API.")



class QueryParam(BaseModel):
    pass

class Line(BaseModel):
    service_types: Literal["Regular", "Night"] = Field(default="Regular")
    mode: Literal[
        "bus", "national-rail", "tube", "dlr", "elizabeth-line", "overground", "cable-car", "river-bus", "tram"
    ]


class QueryParam(BaseModel):
    pass


class StationArrivalQueryParam(BaseModel):
    ids: List[str] = Field(default=["jubilee"])
    stop_point_id: str
    direction: Optional[Literal["inbound", "outbound", "all"]] = Field(default="all")
    destination_station_id: Optional[str]


if __name__ == "__main__":
    LOGGER.info("Testing the src.tfl_api module")

    # set up the environment
    client = TflApiClient()
    res = client.get_line_ids()

    LOGGER.info("Completed job")

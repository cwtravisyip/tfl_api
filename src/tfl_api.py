import io
import logging
import os
import zipfile
from functools import lru_cache
from typing import Dict, List, Literal, Optional, Union

import requests
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_fixed

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO)

class TflApiClient:
    """Custom client for TFL API."""
    
    def __init__(self, headers: Union[Dict, None] = None):
        
        if headers is None:
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



def get_headers_from_env() -> Dict:
    if os.getenv("TFL_ACCESS_KEY") is None:
        raise EnvironmentError("Environment variable `TFL_ACCESS_KEY` is not set.")
    else:
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
        LOGGER.info("Headers is valid for access to TFL API.")


@lru_cache(maxsize=1)
def get_line_ids(service_types: Optional[Literal["Regular", "Night"]] = "Regular") -> List[str]:
    headers = get_headers_from_env()
    endpoint = f"https://api.tfl.gov.uk/Line/Route?{service_types}"
    res = request_endpoint(endpoint, headers=headers)

    # return only the service name, service id, and service mode. Additional data available from res.json()
    return [[service["modeName"], service["id"], service["name"]] for service in res.json()]


def parse_zip_file_response(res: requests.Response):
    # parse the result as
    zip_bytes = io.BytesIO(res.content)
    with zipfile.ZipFile(zip_bytes) as z:
        LOGGER.info(z.namelist())  # see what files are inside

    return zip_bytes


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

    LINE_SERVICE_TYPE = Line(service_types="Regular", mode="tube")
    ENDPOINT_LINE = f"https://api.tfl.gov.uk/Line/Route?{LINE_SERVICE_TYPE.service_types}"
    res = client.request_endpoint(ENDPOINT_LINE)
    LOGGER.info("Completed job")

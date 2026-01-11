"""Module to parse TFL API data responses."""

import io
import pandas
import requests
import zipfile
import logging

logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

JSON_NORMALIZE_KWARGS = {
    "line": {
        "record_path": ["routeSections"], 
        "meta": ["id", "name", "modeName", "lineStatuses", "created", "modified"],
        "record_prefix": "service_",
    },
    # stop point query
    "stop_point": {
        "record_path": ["matches"],
        "meta": ["query", "total", "startIndex", "pageSize"],
        "record_prefix": "stop_",
    }
}


def normalise_json(data: dict, entity: str) -> pandas.DataFrame:
    """Normalise JSON data from TFL API into a pandas DataFrame.

    Args:
        data (dict): JSON data from TFL API.

    Returns:
        pandas.DataFrame: Normalised DataFrame.
    """

    if entity not in JSON_NORMALIZE_KWARGS:
        raise ValueError(f"Entity '{entity}' not recognized. Available entities: {list(JSON_NORMALIZE_KWARGS.keys())}")

    return pandas.json_normalize(data, **JSON_NORMALIZE_KWARGS[entity])

def parse_zip_file_response(res: requests.Response):
    """Parse a zip file response from TFL API.
    
    Some of the TFL API endpoints return zip files. For examble, the `station data detialed` returns `.zip` file.
    This function extracts the contents of the zip file
    """

    # parse the result as
    zip_bytes = io.BytesIO(res.content)
    with zipfile.ZipFile(zip_bytes) as z:
        LOGGER.info(z.namelist())  # see what files are inside

    return zip_bytes

def load_file_from_zip(zip_bytes: io.BytesIO, file_name: str) -> pandas.DataFrame:
    """Load a specific file from a zip archive into a pandas DataFrame.

    Args:
        zip_bytes (io.BytesIO): BytesIO object containing the zip file.
        file_name (str): Name of the file to extract and load.

    Returns:
        pandas.DataFrame: DataFrame containing the data from the specified file.
    """
    with zipfile.ZipFile(zip_bytes) as z:
        with z.open(file_name) as f:
            if file_name not in z.namelist():
                raise FileNotFoundError(f"{file_name} not found in the zip archive.")
            elif file_name.endswith('.csv'):
                df = pandas.read_csv(f)
            else:
                raise ValueError(f"Unsupported file format for {file_name}. Only CSV files are supported.")
    return df
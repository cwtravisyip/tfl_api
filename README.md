# TFL API App

An exploration of the API offering from TFL. The current development require the environment variable `TFL_ACCESS_KEY`. Alternatively, the access key could be parsed into the `src.tfl_api.TflApiClient` object at instantiation as the value tothe headers argument:
```python
HEADERS = {"app_key": "TFL_ACCESS_KEY", "content-type": "application/json"}
client = TflApiClient(headers = headers)
```

The client object has a `requests_endpoint` method which helps with handling the query sent to the API.

```python
# set up the environment
client = TflApiClient()

LINE_SERVICE_TYPE = Line(service_types="Regular", mode="tube")
ENDPOINT_LINE = f"https://api.tfl.gov.uk/Line/Route?{LINE_SERVICE_TYPE.service_types}"
res = client.request_endpoint(ENDPOINT_LINE)
LOGGER.info("Completed job")
```

## Endpoint
TFL API offers a series of endpoints. This repository mainly focus on the following:
* Line
* Staion
* Arrival Time

## References
https://api-portal.tfl.gov.uk
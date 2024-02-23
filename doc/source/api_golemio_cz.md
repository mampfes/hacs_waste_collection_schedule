# Praha - Czech Republic

Support for schedules provided by [Golemio API](https://api.golemio.cz/docs/openapi/), open data platform for Prague, CZ.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: api_golemio_cz
      args:
        lat: LAT
        lon: LON
        radius: RADIUS
        api_key: API_KEY
        ignored_containers:
          - 123
          - 456
        auto_suffix: True
        suffix: SUFFIX
```

### Configuration Variables

**lat** _integer (required)_: Latitude of the location. 

**lon** _integer (required)_: Longitude of the location.

**radius** _integer (required)_: Radius from the defined location, use low value to select a single separation point.

**api_key** _string (required)_: API key for Golemio API, see below.

**only_monitored** _boolean (optional)_: Only return monitored containers (the state is not reported by the integration though).

**ignored_containers**: _list of integers (optional)_: List of IDs for containers to ignore. 

**auto_suffix**: _boolean (optional)_: Automatically append address as the suffix to all containers found in this query.

**suffix**: _string (optional)_: Suffix to append to all containers found in this query.


## Example
```yaml
waste_collection_schedule:
    sources:
    - name: api_golemio_cz
      args:
        lat: 50.104802397741665
        lon: 14.538238985303936
        radius: 1
        api_key: !secret golemio_api_key
        suffix: " - Chvalská"
        ignored_containers: 
          - 35895
```

## Getting the API key

To get the API key, you must register at the Golemio site with a verified e-mail address. Follow instructions at the [Golemio site](https://api.golemio.cz/api-keys) and save the generated token to your `secrets.yaml`.

## Using suffix and auto_suffix

The `suffix` and `auto_suffix` arguments are used to append text to the end of the container types. This is useful when you have multiple containers with the same type, but in different locations. The `suffix` is generally useful if you have multiple config entries, each targeting a single separation point, while the `auto_suffix` is essentially necessary to use queries that return multiple separation points, each container will be then appended with an address (e.g. `Papír - Oktábcových 1039/1`). If both arguments are supplied, `suffix` is appended after the auto-generated suffix.

## Ignoring containers

Sometimes you don't want to get all containers, for example if a pick date is not provided for the container and a warning is shown in the logs. You can use `ignored_containers` list to exclude these containers from the result.

## Note on calculation of collection dates

The API provides only a single future date in a single query. However, the schema contains information about weekdays and frequency of the collection which are used for calculation of other dates. Currently, the integration calculates one past date (or today's date, because the API does not return the collection date if it's today) and future dates to return 10 dates for every container returned in the query.

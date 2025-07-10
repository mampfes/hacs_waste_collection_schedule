# Cyclad

Support for schedules provided by [Cyclad](https://cyclad.org/).

Example city supported: Nancras (ID 254).

## Configuration via configuration.yaml
```yaml
waste_collection_schedule:
    sources:
    - name: cyclad_org
      args:
        commune_id: 254
```

### Configuration Variables

**commune_id**
*(integer) (required)*

The numeric identifier of your town. A list of available IDs can be fetched from
`https://cyclad.org/wp-json/vernalis/v1/communes`.

## Example
```yaml
waste_collection_schedule:
    sources:
    - name: cyclad_org
      args:
        commune_id: 254
```

## How to get the source argument

Request `https://cyclad.org/wp-json/vernalis/v1/communes` and search for your
town to obtain the `commune_id`.

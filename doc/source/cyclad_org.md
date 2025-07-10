# Cyclad — provider for waste management schedules

Support for schedules provided by [Cyclad](https://cyclad.org/).

The list of available communes can be retrieved from <https://cyclad.org/wp-json/vernalis/v1/communes>.
The value of `ID` for your commune must be used as `city_id` in the configuration.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cyclad_org
      args:
        city_id: 254
```

### Configuration variables

**city_id**
*(integer) (required)* ID of your commune from the [Cyclad communes list](https://cyclad.org/wp-json/vernalis/v1/communes).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: cyclad_org
      args:
        city_id: 254
```

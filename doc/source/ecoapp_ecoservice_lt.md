# UAB "Ecoservice"

Support for schedules provided by [UAB "Ecoservice"](https://ecoservice.lt), Lithuania.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ecoapp_ecoservice_lt
      args:
        waste_object_ids:
          - id1
          - id2
```

### Configuration Variables

**waste_object_ids**  
_(list) (required)_

## Examples

```yaml
waste_collection_schedule:
  sources:
    - name: ecoapp_ecoservice_lt
      args:
        waste_object_ids:
          - 13-L-115261
          - 13-P-505460
          - 13-S-500496
```

```yaml
waste_collection_schedule:
  sources:
    - name: ecoapp_ecoservice_lt
      args:
        waste_object_ids:
          - 13-L-115261
```

## How to get the source arguments

1. Go to Ecoservice schedules at [Ecoservice grafikai](https://ecoservice.lt/grafikai/)
2. Enter your address into the search "by address"
3. Select your address in the dropdown, get a list of your containers.
4. Container id ("waste_object_id") should be in the format similar to "13-L-115261". NB: containers without Container id are not supported yet.

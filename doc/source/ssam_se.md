# SSAM (Deprecated)

This integration is deprecated and will probably not work forever. Please use the [edpevent_se source](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/edpevent_se.md) instead.

Support for schedules provided by [SSAM](https://ssam.se/mitt-ssam/hamtdagar.html), serving the municipality of Lessebo, Tingsryd, Älmhult, Markaryd and Växjö Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ssam_se
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ssam_se
      args:
        street_address: Andvägen 3, Växjö
```

## How to get the source argument

The source argument is the address to the house with waste collection. The address can be tested [here](https://ssam.se/mitt-ssam/hamtdagar.html).

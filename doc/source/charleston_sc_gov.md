# Charleston, SC

Support for garbage and trash collection schedules published by the [City of Charleston Environmental Services Division](https://www.charleston-sc.gov/345/Environmental-Services).

The city's service territory includes areas in Charleston and Berkeley counties. Depending on the address, collection is performed by City crews or Trident Waste.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: charleston_sc_gov
      args:
        address: ADDRESS
```

### Configuration Variables

**address**
*(string) (required)*

Full street address including city, state, and ZIP code.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: charleston_sc_gov
      args:
        address: "123 Coming St, Charleston, SC 29403"
```

The source looks up the address in the city's live garbage and trash/yard-waste collection-area maps. Garbage and trash/yard-waste are collected on independent routes and can fall on different weekdays for the same address, so the source queries both layers and returns two separate weekly streams, `Garbage` and `Trash & Yard Waste`, each on its own collection day. An address that falls inside only one of the two route layers still returns that single stream. Temporary holiday or emergency delays announced by the city are not represented in the route layers.

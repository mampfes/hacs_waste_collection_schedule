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

The source looks up the address in the city's live garbage and trash collection-area map and returns its weekly collection day. Temporary holiday or emergency delays announced by the city are not represented in the route layer.

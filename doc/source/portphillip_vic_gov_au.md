# City of Port Phillip

Support for schedules provided by [City of Port Phillip](https://www.portphillip.vic.gov.au/council-services/waste-recycling-and-rubbish/bins-and-collection-services), Victoria, Australia.

The council collects general waste, recycling and FOGO (Food Organics and Garden Organics) bins together, once a week, on the same day.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: portphillip_vic_gov_au
      args:
        address: ADDRESS
```

### Configuration Variables

**address**
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: portphillip_vic_gov_au
      args:
        address: "9 Spray Street Elwood"
```

## How to get the source arguments

Visit the [City of Port Phillip bins and collection services](https://www.portphillip.vic.gov.au/council-services/waste-recycling-and-rubbish/bins-and-collection-services) page and search for your address in the map widget's search bar.

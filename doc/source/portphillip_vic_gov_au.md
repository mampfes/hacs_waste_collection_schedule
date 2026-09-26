# City of Port Phillip

Support for schedules provided by [City of Port Phillip](https://www.portphillip.vic.gov.au).

Source for City of Port Phillip waste collection.

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
        address: 9 Spray Street Elwood
```

## How to get the source arguments

Enter your street address including suburb (e.g. '9 Spray Street Elwood'). Search at https://www.portphillip.vic.gov.au/council-services/waste-recycling-and-rubbish/bins-and-collection-services

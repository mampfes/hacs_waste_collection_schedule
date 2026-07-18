# Bathurst Regional Council

Support for schedules provided by [Bathurst Regional Council](https://www.bathurst.nsw.gov.au/Services/Waste-Recycling/Waste-Recycling-Calendar).

Source for Bathurst Regional Council (NSW) waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bathurst_nsw_gov_au
      args:
        address: ADDRESS
        suburb: SUBURB
```

### Configuration Variables

**address**  
*(string) (required)*

**suburb**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: bathurst_nsw_gov_au
      args:
        address: 230 Howick St
        suburb: Bathurst
```

## How to get the source arguments

Enter your street address and suburb (e.g. address '230 Howick St', suburb 'Bathurst'). Search at https://maps.bathurst.nsw.gov.au/IntraMaps23A/ApplicationEngine/frontend/mapbuilder/default.htm?configId=00000000-0000-0000-0000-000000000000&liteConfigId=24d1884e-fc58-45df-bca0-11bddc554781

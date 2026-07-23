# Bathurst Regional Council

Support for schedules provided by [Bathurst Regional Council](https://www.bathurst.nsw.gov.au/Services/Waste-Recycling/Waste-Recycling-Calendar), New South Wales, Australia.

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
        address: "230 Howick St"
        suburb: "Bathurst"
```

## How to get the source arguments

Visit the [Bathurst waste collection map](https://maps.bathurst.nsw.gov.au/IntraMaps23A/ApplicationEngine/frontend/mapbuilder/default.htm?configId=00000000-0000-0000-0000-000000000000&liteConfigId=24d1884e-fc58-45df-bca0-11bddc554781) and search for your property. Use the street address and suburb shown in the search results.

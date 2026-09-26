# Stirling Council

Support for schedules provided by [Stirling Council](https://www.stirling.gov.uk/).

Source for Stirling Council waste collection services.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: stirling_gov_uk
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
    - name: stirling_gov_uk
      args:
        address: 38 Kildean Road
```

## How to get the source arguments

Visit https://www.stirling.gov.uk/bins-and-recycling/bin-collection-dates-search/ and type your address into the search to see the exact wording, then use the same here. House number and street (e.g. '38 Kildean Road'), property name (e.g. 'Merlo'), or a single-dwelling postcode work.

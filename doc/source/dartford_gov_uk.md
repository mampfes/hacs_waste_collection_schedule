# Dartford Borough Council

Support for schedules provided by [Dartford Borough Council](https://dartford.gov.uk).

Source for Dartford Borough Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: dartford_gov_uk
      args:
        uprn: UPRN
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: dartford_gov_uk
      args:
        uprn: '100060862889'
```

## How to get the source arguments

Your UPRN is displayed in the top left corner of the Dartford website when you are viewing your collection schedule, or look it up on https://www.findmyaddress.co.uk/.

# Chelmsford City Council

Support for schedules provided by [Chelmsford City Council](https://www.chelmsford.gov.uk/).

Source for Chelmsford City Council, UK

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: chelmsford_gov_uk
      args:
        collection_round: COLLECTION_ROUND
```

### Configuration Variables

**collection_round**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: chelmsford_gov_uk
      args:
        collection_round: Tuesday A
```

## How to get the source arguments

You can find your collection round (e.g. Tuesday A) by visiting https://www.chelmsford.gov.uk/bins-and-recycling/check-your-collection-day and entering in your address details.

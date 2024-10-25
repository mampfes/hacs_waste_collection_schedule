# Chelmsford City Council

Support for schedules provided by [Chelmsford City Council](https://www.chelmsford.gov.uk), serving Chelmsford, Essex, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: chelmsford_gov_uk
      args:
        collection_round: "Collection Round"
```

### Configuration Variables

**collection_round**  
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: chelmsford_gov_uk
      args:
        collection_round: "Tuesday B"
```

## How to get the source argument

You can find your collection round by visiting <https://www.chelmsford.gov.uk/bins-and-recycling/check-your-collection-day> and entering in your address details.

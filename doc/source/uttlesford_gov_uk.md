# Uttlesford District Council

Support for schedules provided by [Uttlesford District Council](https://www.uttlesford.gov.uk).

Source for uttlesford.gov.uk, Uttlesford District Council, UK

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: uttlesford_gov_uk
      args:
        house: HOUSE
```

### Configuration Variables

**house**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: uttlesford_gov_uk
      args:
        house: 29142-Tuesday
```

## How to get the source arguments

Go to https://bins.uttlesford.gov.uk/ and look up your address. The house value is the `house` parameter of the results page address (`collections.php?house=29142-Tuesday`).

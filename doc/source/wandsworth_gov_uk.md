# Wandsworth Council

Support for schedules provided by [Wandsworth Council](https://www.wandsworth.gov.uk).

Source for Wandsworth Council for the London Borough of Wandsworth, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: wandsworth_gov_uk
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
    - name: wandsworth_gov_uk
      args:
        uprn: 100022659217
```

## How to get the source arguments

You can find your UPRN by visiting [Find My Address](https://www.findmyaddress.co.uk) and entering your address details.

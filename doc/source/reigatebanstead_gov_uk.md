# Reigate & Banstead Borough Council

Support for schedules provided by [Reigate & Banstead Borough Council](https://reigate-banstead.gov.uk).

Source for reigate-banstead.gov.uk services for the Reigate & Banstead Borough, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: reigatebanstead_gov_uk
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
    - name: reigatebanstead_gov_uk
      args:
        uprn: 68110755
```

## How to get the source arguments

Find your UPRN at https://www.findmyaddress.co.uk/

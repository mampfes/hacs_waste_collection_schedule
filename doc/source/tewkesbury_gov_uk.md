# Tewkesbury Borough Council

Support for schedules provided by [Tewkesbury Borough Council](https://www.tewkesbury.gov.uk).

Home waste collection schedule for Tewkesbury Borough Council

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: tewkesbury_gov_uk
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
    - name: tewkesbury_gov_uk
      args:
        uprn: 100120544973
```

## How to get the source arguments

Enter your UPRN; you can look it up on https://www.findmyaddress.co.uk/.

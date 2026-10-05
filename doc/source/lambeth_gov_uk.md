# London Borough of Lambeth

Support for schedules provided by [London Borough of Lambeth](https://www.lambeth.gov.uk/).

Source for London Borough of Lambeth

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: lambeth_gov_uk
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
    - name: lambeth_gov_uk
      args:
        uprn: '100021893293'
```

## How to get the source arguments

Find your UPRN at https://www.findmyaddress.co.uk/

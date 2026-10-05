# London Borough of Tower Hamlets

Support for schedules provided by [London Borough of Tower Hamlets](https://www.towerhamlets.gov.uk/).

Source for London Borough of Tower Hamlets

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: tower_hamlets_gov_uk
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
    - name: tower_hamlets_gov_uk
      args:
        uprn: '6085613'
```

## How to get the source arguments

Find your UPRN at https://www.findmyaddress.co.uk/

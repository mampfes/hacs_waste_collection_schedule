# London Borough of Tower Hamlets

Support for schedules provided by [London Borough of Tower Hamlets](https://www.towerhamlets.gov.uk/), serving Tower Hamlets, London, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: tower_hamlets_gov_uk
      args:
        uprn: "UPRN"
```

### Configuration Variables

**uprn**  
_(String | Integer) (required)_

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: tower_hamlets_gov_uk
      args:
        uprn: "6085613"
```

## How to get the source argument

Get your Unique Property Reference Number (UPRN) by going to <https://www.findmyaddress.co.uk/> and entering your address details.

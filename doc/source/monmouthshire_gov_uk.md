# Monmouthshire Council

Support for schedules provided by [Monmouthshire Council](https://www.monmouthshire.gov.uk), UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: monmouthshire_gov_uk
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
    - name: monmouthshire_gov_uk
      args:
        uprn: "200000952833"
```

## How to get the source argument

An easy way to discover your Unique Property Reference Number (UPRN) is by going to [Find My Address](https://www.findmyaddress.co.uk) and entering your address details.

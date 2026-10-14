# Enfield Council

Support for schedules provided by [Enfield Council](https://www.enfield.gov.uk/services/rubbish-and-recycling/find-my-collection-day).

Source for Enfield Council, London, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: enfield_gov_uk
      args:
        uprn: UPRN
        address: ADDRESS
```

### Configuration Variables

**uprn**  
*(string) (optional)*

**address**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: enfield_gov_uk
      args:
        uprn: '207102166'
```

## How to get the source arguments

Search for your address on the Enfield Council collection-day page. If address lookup is ambiguous, use your UPRN from [Find My Address](https://www.findmyaddress.co.uk/).

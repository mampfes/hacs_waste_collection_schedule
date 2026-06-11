# Enfield Council

Support for schedules provided by [Enfield Council](https://www.enfield.gov.uk/services/rubbish-and-recycling/find-my-collection-day), London, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: enfield_gov_uk
      args:
        uprn: UPRN
```

### Configuration Variables

**uprn**
*(string) (optional)*

**address**
*(string) (optional)*

You must provide either `uprn` or `address`.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: enfield_gov_uk
      args:
        address: 127 Palmerston Rd, London N22 8QX
```

```yaml
waste_collection_schedule:
  sources:
    - name: enfield_gov_uk
      args:
        uprn: "207102166"
```

## How to get the source arguments

Search for your property on the [Enfield Council collection-day page](https://www.enfield.gov.uk/services/rubbish-and-recycling/find-my-collection-day). If address matching is ambiguous, find your UPRN at [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/).

# Derbyshire Dales District Council

Support for schedules provided by [Derbyshire Dales District Council](https://www.derbyshiredales.gov.uk/).

Source for derbyshiredales.gov.uk services for Derbyshire Dales, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: derbyshiredales_gov_uk
      args:
        address_id: ADDRESS_ID
```

### Configuration Variables

**address_id**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: derbyshiredales_gov_uk
      args:
        address_id: DE4 3GS
```

## How to get the source arguments

Your property's UPRN, find it at https://www.findmyaddress.co.uk/. You can also use a Postcode.

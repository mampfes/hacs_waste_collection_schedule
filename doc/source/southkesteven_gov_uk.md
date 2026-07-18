# South Kesteven District Council

Support for schedules provided by [South Kesteven District Council](https://southkesteven.gov.uk).

Source for southkesteven.gov.uk services for South Kesteven, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: southkesteven_gov_uk
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
    - name: southkesteven_gov_uk
      args:
        address_id: PE10 0RX
```

## How to get the source arguments

Your property's UPRN, find it at https://www.findmyaddress.co.uk/. You can also use a Postcode.

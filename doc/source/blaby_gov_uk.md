# Blaby District Council

Support for schedules provided by [Blaby District Council](https://my.blaby.gov.uk/collections), serving the Blaby district, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: blaby_gov_uk
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
    - name: blaby_gov_uk
      args:
        uprn: "100030395499"
```

## How to get the source argument

An easy wasy of finding your UPRN is to search for your address on the [FindMyAddress service](https://www.findmyaddress.co.uk/) which displays the UPRN in the result.

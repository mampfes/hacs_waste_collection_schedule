# London Borough of Southwark

Support for schedules provided by [London Borough of Southwark](https://www.southwark.gov.uk/), UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: southwark_gov_uk
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
    - name: southwark_gov_uk
      args:
        uprn: "200003455089"
```

## How to get the source argument

An easy way of finding your UPRN is by going to [FindMyAddress service](https://www.findmyaddress.co.uk/) and entering in your address details.
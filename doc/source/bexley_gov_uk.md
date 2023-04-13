# London Borough of Bexley

Support for schedules provided by the [London Borough of Bexley](https://mybexley.bexley.gov.uk/service/When_is_my_collection_day), serving the London Borough of Bexley, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bexley_gov_uk
      args:
        uprn: UPRN_CODE
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: bexley_gov_uk
      args:
        uprn: "100020194783"
```

## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering your address details.

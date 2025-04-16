# London Borough of Bexley

Support for schedules provided by the [London Borough of Bexley](https://waste.bexley.gov.uk/waste), serving the London Borough of Bexley, UK. 

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bexley_gov_uk
      args:
        uprn: UPRN_CODE
```

### Configuration Variables

**uprn**<br>
*(string) (required)*

Unique number the  London Borough of Bexley uses to identify your property.

#### How to find your `UPRN`
An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering your address details.


## Example

```yaml
waste_collection_schedule:
  sources:
    - name: bexley_gov_uk
      args:
        uprn: "100020194783"
```


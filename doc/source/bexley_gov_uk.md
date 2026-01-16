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

Unique number used to identify your property.

#### How to find your `UPRN`

You can find your `UPRN` by searching for your address on the [Bexley Council website](https://waste.bexley.gov.uk/waste), You will then see the UPRN in the URL of the page. For example, if the URL is `https://waste.bexley.gov.uk/waste/100020194783`, then your UPRN is `100020194783`.

Another way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering your address details.


## Example

```yaml
waste_collection_schedule:
  sources:
    - name: bexley_gov_uk
      args:
        uprn: "100020194783"
```


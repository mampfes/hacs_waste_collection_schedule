# South Ayrshire Council

Support for schedules provided by [South Ayrshire Council](https://www.south-ayrshire.gov.uk), serving South Ayrshire, Scotland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: south_ayrshire_gov_uk
      args:
        postcode: KA7 3XH
        uprn: "141030966"
```

### Configuration Variables

**postcode**
*(string) (required)*
Your postcode, e.g. `KA7 3XH`.

**uprn**
*(string or integer) (required)*
Your Unique Property Reference Number (UPRN). To find your UPRN, visit the [South Ayrshire bin collection days page](https://www.south-ayrshire.gov.uk/article/23931/Bin-collection-days), enter your postcode, and note the value in the address dropdown (shown in the page source or via your browser's developer tools). You can also look up your UPRN at [FindMyAddress](https://www.findmyaddress.co.uk/search) or similar services.

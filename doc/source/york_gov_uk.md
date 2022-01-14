# York Council

Support for schedules provided by [York Council](https://myaccount.york.gov.uk/bin-collections), serving the city of York, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: york_gov_uk
      args:
        uprn: UPRN_CODE
```

### Configuration Variables

**uprn**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: york_gov_uk
      args:
        uprn: "100050580641"
```

## How to get the source argument

The UPRN code can be found in the network request when entering your postcode and selecting your address on the [York Waste Collection Calendar page](https://myaccount.york.gov.uk/bin-collections). You should look for a request like `https://waste-api.york.gov.uk/api/GetBinCollectionLocationForUprn/010093236548` the last segment is your UPRN code.

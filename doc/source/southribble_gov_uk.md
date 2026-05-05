# South Ribble Borough Council

Support for schedules provided by [South Ribble Borough Council](https://www.southribble.gov.uk), UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: southribble_gov_uk
      args:
        postcode: POSTCODE
        uprn: UPRN
```

### Configuration Variables

**postcode**  
*(string) (required)*

Your postcode, e.g. `PR25 1DH`.

**uprn**  
*(string) (required)*

The UPRN for your address. To find this, go to https://www.southribble.gov.uk/bincollectiondays, enter your postcode, right-click your address in the dropdown and select "Inspect" to find the `<option value="...">` value.

## Examples

```yaml
waste_collection_schedule:
  sources:
    - name: southribble_gov_uk
      args:
        postcode: "PR25 1DH"
        uprn: "100012755948"
```

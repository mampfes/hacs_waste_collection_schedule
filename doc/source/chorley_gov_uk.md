# Chorley Council

Support for schedules provided by [Chorley Council](https://www.chorley.gov.uk), UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: chorley_gov_uk
      args:
        postcode: POSTCODE
        uprn: UPRN
```

### Configuration Variables

**postcode**  
*(string) (required)*

Your postcode, e.g. `PR6 7YD`.

**uprn**  
*(string) (required)*

The UPRN for your address. To find this, go to https://www.chorley.gov.uk/bincollectiondays, enter your postcode, right-click your address in the dropdown and select "Inspect" to find the `<option value="...">` value.

## Examples

```yaml
waste_collection_schedule:
  sources:
    - name: chorley_gov_uk
      args:
        postcode: "PR6 7YD"
        uprn: "010091497098"
```

# Wirral Council

Support for schedules provided by [Wirral Council](https://wirral.gov.uk/), UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: wirral_gov_uk
      args:
        postcode: POSTCODE
        address_value: ADDRESS_VALUE
```

### Configuration Variables

**postcode**  
*(string) (required)*

Your postcode, e.g. `CH49 4NP`.

**address_value**  
*(string) (required)*

The 12-digit address value from the dropdown on the Wirral bin calendar page. To find this, go to https://www.wirral.gov.uk/bincal_dev/, enter your postcode, right-click your address in the dropdown and select "Inspect" to find the `<option value="...">` value.

## Examples

```yaml
waste_collection_schedule:
  sources:
    - name: wirral_gov_uk
      args:
        postcode: "CH49 4NP"
        address_value: "000042037487"
```

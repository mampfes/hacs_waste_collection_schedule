# Perth and Kinross Council

Support for schedules provided by [Perth and Kinross Council](https://www.pkc.gov.uk), UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: pkc_gov_uk
      args:
        uprn: UPRN
```

### Configuration Variables

**uprn**
*(string) (required)*

Your Unique Property Reference Number (UPRN).

## How to find your UPRN

1. Visit the [Perth and Kinross bin collection dates page](https://my.pkc.gov.uk/AchieveForms/?form_uri=sandbox-publish://AF-Process-de9223b1-a7c6-408f-aaa3-aee33fd7f7fa/AF-Stage-9fa33e2e-4c1b-4963-babf-4348ab8154bc/definition.json) and search for your address using your street name or postcode.
2. Select your address from the dropdown list, then right-click it and choose `Inspect` (or `Inspect Element`) — the selected `<option>` element's `value` attribute is your UPRN.
3. Alternatively, look up your address at [findmyaddress.co.uk](https://www.findmyaddress.co.uk/).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: pkc_gov_uk
      args:
        uprn: "124022910"
```

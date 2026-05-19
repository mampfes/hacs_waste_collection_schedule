# South Lanarkshire Council, United Kingdom

Support for schedules provided by [South Lanarkshire Council](https://wasteservices.southlanarkshire.gov.uk), serving South Lanarkshire, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: southlanarkshire_gov_uk
      args:
        postcode: POSTCODE
        uprn: UPRN
```

### Configuration Variables

**postcode**
*(String) (required)*

Your property's postcode (e.g. `G73 1UR`).

**uprn**
*(Integer) (required)*

The Unique Property Reference Number (UPRN) for your property (e.g. `484000600`).

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: southlanarkshire_gov_uk
      args:
        postcode: "G73 1UR"
        uprn: 484000600
```

## How to get the source arguments

1. Go to <https://wasteservices.southlanarkshire.gov.uk/PublicDashboard>.
2. Your **UPRN** can be found using the [FindMyAddress](https://www.findmyaddress.co.uk/search) or [UPRN.uk](https://uprn.uk) lookup tools — search for your full address and note the UPRN shown.

Alternatively, after entering your postcode on the South Lanarkshire portal and selecting your property, you can inspect the property dropdown option (right-click → Inspect Element) and use the numeric value in the `value=` attribute of the selected `<option>` tag.

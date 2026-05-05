# London Borough of Hounslow

Support for schedules provided by [London Borough of Hounslow](https://hounslow.gov.uk), serving London Borough of Hounslow, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: hounslow_gov_uk
      args:
        uprn: "UPRN"

```

### Configuration Variables

**uprn**
*(String | Integer) (required)*


## Example

```yaml
waste_collection_schedule:
    sources:
    - name: hounslow_gov_uk
      args:
        uprn: "100021552942"

```

## How to get the source argument

### Using findmyaddress.co.uk

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.

### Using the Hounslow self-service portal

- Go to <https://my.hounslow.gov.uk/en/service/Waste_and_recycling_collections>
- Click "continue without an account" and proceed to the address lookup step
- Enter your postcode and select your address from the dropdown
- Right-click the address dropdown and select `Inspect` or `Inspect Element`
- Find the selected `<option>` element — the `value` attribute is your UPRN

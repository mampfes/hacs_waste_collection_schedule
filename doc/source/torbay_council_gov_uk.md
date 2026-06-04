# Torbay Council

Support for schedules provided by [Torbay Council](https://www.torbay.gov.uk/), Devon, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: torbay_council_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**uprn** _(string) (required)_
Your Unique Property Reference Number (UPRN).

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: torbay_council_gov_uk
      args:
        uprn: "100040542066"
```

## How to find your UPRN

An easy way to find your Unique Property Reference Number (UPRN) is by going to [Find My Address](https://www.findmyaddress.co.uk/) and entering your address details.

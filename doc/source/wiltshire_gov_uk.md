# Wiltshire Council

Support for schedules provided by [Wiltshire Council](https://wiltshire.gov.uk/).

If collection data is available for the address provided, it will return household and recycling waste collection dates.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: wiltshire_gov_uk
      args:
        postcode: POSTCODE
        uprn: UPRN
```

### Configuration Variables

**postcode**<br>
*(string) (required)*

**uprn**<br>
*(string) (required)*

Both the postcode and the UPRN should be supplied in the arguments.

## Examples

```yaml
waste_collection_schedule:
  sources:
    - name: wiltshire_gov_uk
      args:
        postcode: BA149QP
        uprn: 100121085972
```

## How to find your UPRN

An easy way to discover your Unique Property Reference Number (UPRN) is by going to [Find My Address](https://www.findmyaddress.co.uk/) and providng your address details.
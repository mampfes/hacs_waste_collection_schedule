# Northumberland County Council

Support for schedules provided by [Northumberland County Council](https://www.northumberland.gov.uk), serving Northumberland, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: northumberland_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**uprn**
*(string) (required)*

Your Unique Property Reference Number (UPRN).

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: northumberland_gov_uk
      args:
        uprn: "100110637553"
```

## How to find your UPRN

An easy way to find your UPRN is by going to <https://www.findmyaddress.co.uk/> and entering your address details.

Alternatively, visit <https://bincollection.northumberland.gov.uk/postcode>, enter your postcode, and select your address. The UPRN is shown in the address dropdown option value.

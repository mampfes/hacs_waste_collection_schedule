# Newcastle Under Lyme Borough Council

Support for schedules provided by [Newcastle Under Lyme Borough Council](https://www.newcastle-staffs.gov.uk/waste)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: newcastle_staffs_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**uprn**  
*(string) (required)*

This is required to unambiguously identify the property.

## Example using UPRN

```yaml
waste_collection_schedule:
    sources:
    - name: newcastle_staffs_gov_uk
      args:
        uprn: "100031736973"
```

## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.

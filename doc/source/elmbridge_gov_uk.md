# Elmbridge Borough Council

Support for schedules provided by [Elmbridge Borough Council](http://elmbridge-self.achieveservice.com/service/Your_bin_collection_days), serving Elmbridge, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: elmbridge_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**uprn**  
*(string) (required)*

This is required to unambiguously identify the property.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: elmbridge
      args:
        uprn: "10013119164"

```

## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.

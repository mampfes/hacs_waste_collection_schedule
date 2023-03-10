# Binzone

Consolidated support for schedules provided by South Oxfordshire District Council and Vale of White Horse District Council

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: binzone_uk
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
    - name: binzone_uk
      args:
        uprn: 100120883950
```

## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.

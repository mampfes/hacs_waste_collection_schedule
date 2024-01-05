# Tewkesbury City Council

Support for upcoming schedules provided by [Tewkesbury City Council](https://tewkesbury.gov.uk/services/waste-and-recycling/), serving Tewkesbury (UK) and areas of Gloucestershire.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: tewkesbury_gov_uk
      args:
        uprn: UNIQUE PROPERTY REFERENCE NUMBER
```

### Configuration Variables

**UPRN**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: tewkesbury_gov_uk
      args:
        uprn: 100120544973
```

## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering your address details.

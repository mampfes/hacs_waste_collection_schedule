# Wakefield Council

Support for schedules provided by [Wakefield Council](https://www.wakefield.gov.uk/), serving the district of Wakefield, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: wakefield_gov_uk
      args:
        uprn: Unique Property Reference Number (UPRN)
```

### Configuration Variables

**uprn**
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: wakefield_gov_uk
      args:
        uprn: "63024087"
```

## How to find the values for arguments above

You can find your UPRN by going to the [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/) and searching there.

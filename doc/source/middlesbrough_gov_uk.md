# Middlesbrough Council

Support for schedules provided by [Middlesbrough Council](https://www.middlesbrough.gov.uk/bin-collection-dates).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: middlesbrough_gov_uk
      args:
        uprn: UPRN_CODE
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Example using UPRN

```yaml
waste_collection_schedule:
    sources:
    - name: middlesbrough_gov_uk
      args:
        uprn: "100110140843"
```

## How to get the source argument

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.

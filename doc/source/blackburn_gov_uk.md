# Blackburn with Darwen Borough Council

Support for schedules provided by [Blackburn with Darwen Borough Council](https://mybins.blackburn.gov.uk/), UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: blackburn_gov_uk
      args:
        uprn: UPRN_CODE
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: blackburn_gov_uk
      args:
        uprn: "10091617919"
```

## How to get the source argument

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
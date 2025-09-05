# Wrexham County Borough Council

Support for schedules provided by [Wrexham Borough Council](https://www.wrexham.gov.uk/), serving the city of Wrexham, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: wrexham_gov_uk
      args:
        uprn: "UPRN"
```

### Configuration Variables

**uprn**  
*(String | Integer) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: wrexham_gov_uk
      args:
        uprn: "100100940408"
```

## How to get the source argument

Use your Unique Property Reference Number (UPRN) as the `uprn` argument.

The easiest way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
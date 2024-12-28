# Knowsley Council

Support for schedules provided by [Knowsley Council](https://www.knowsley.gov.uk/), serving Knowsley Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: knowsley_gov_uk
      args:
        postcode: POSTCODE
        uprn: UPRN
```

### Configuration Variables

**postcode**  
*(String) (required)*

**uprn**  
*(String | Integer) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: knowsley_gov_uk
      args:
        postcode: L364AR
        uprn: "000040082756"
```

```yaml
waste_collection_schedule:
    sources:
    - name: knowsley_gov_uk
      args:
        postcode: L34 0HZ
        uprn: 40029195
```

## How to get the source argument

Use your postcode as the `postcode` argument and your Unique Property Reference Number (UPRN) as the `uprn` argument.

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.

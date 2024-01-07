# London Borough of Harrow

Support for schedules provided by [London Borough of Harrow](https://www.harrow.gov.uk/), UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: harrow_gov_uk
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
    - name: harrow_gov_uk
      args:
        uprn: "100060218986"
```

## How to get the source argument

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
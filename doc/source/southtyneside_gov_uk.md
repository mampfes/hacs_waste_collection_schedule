# South Tyneside Council

Support for schedules provided by [South Tyneside Council](https://www.southtyneside.gov.uk/article/1023/Bin-collection-dates), serving South Tyneside, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: southtyneside_gov_uk
      args:
        postcode: POSTCODE
        uprn: UPRN_CODE
```

### Configuration Variables

**postcode**  
*(string) (required)*

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: southtyneside_gov_uk
      args:
        postcode: "NE34 8RY"
        uprn: "100000342955"
```

## How to get the uprn argument above

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.

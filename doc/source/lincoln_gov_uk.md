# City Of Lincoln Council

Support for schedules provided by [City Of Lincoln Council](https://www.lincoln.gov.uk/), serving City of Lincoln, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: lincoln_gov_uk
      args:
        postcode: POSTCODE
        uprn: "UPRN"
        
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
    - name: lincoln_gov_uk
      args:
        postcode: LN5 7SH
        uprn: "000235024846"
```

## How to get the source argument

Use your postcode as the `postcode` argument and your Unique Property Reference Number (UPRN) as the `uprn` argument.

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details. 

Alternatively use the developer inspection tools (right cklick inspect / F12) to inspect the select address `select` item. The `value` of the of the `option` item containing your address is your `uprn`

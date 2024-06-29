# Vale of Glamorgan Council

Support for schedules provided by [Vale of Glamorgan Council](https://valeofglamorgan.gov.uk/), serving Vale of Glamorgan Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: valeofglamorgan_gov_uk
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
    - name: valeofglamorgan_gov_uk
      args:
        uprn: "64003486"
        
```

## How to get the source argument

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.

Alternatively, you can find your UPRN by inspecting the source code of the Vale of Glamorgan Council's waste collection page after entering your postcode.

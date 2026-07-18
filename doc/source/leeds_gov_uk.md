# Leeds City Council

Support for schedules provided by [Leeds City Council](https://www.leeds.gov.uk/bins-and-recycling).

Source for Leeds City Council bin collections.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: leeds_gov_uk
      args:
        uprn: UPRN
        api_key: API_KEY
```

### Configuration Variables

**uprn**  
*(string) (required)*

**api_key**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: leeds_gov_uk
      args:
        uprn: '72306030'
```

## How to get the source arguments

Provide your UPRN (Unique Property Reference Number); find it at https://www.findmyaddress.co.uk/. The API Key is optional: leave it blank to use the council's embedded public key, and only set it if the council rotates the key.

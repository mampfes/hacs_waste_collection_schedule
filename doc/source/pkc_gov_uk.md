# Perth and Kinross Council

Support for schedules provided by [Perth and Kinross Council](https://www.pkc.gov.uk).

Source for Perth and Kinross Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: pkc_gov_uk
      args:
        uprn: UPRN
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: pkc_gov_uk
      args:
        uprn: '124022910'
```

## How to get the source arguments

Find your UPRN by searching for your address at https://my.pkc.gov.uk/AchieveForms/?mode=fill&consentMessage=yes&form_uri=sandbox-publish://AF-Process-de9223b1-a7c6-408f-aaa3-aee33fd7f7fa/AF-Stage-9fa33e2e-4c1b-4963-babf-4348ab8154bc/definition.json&process=1&process_uri=sandbox-processes://AF-Process-de9223b1-a7c6-408f-aaa3-aee33fd7f7fa&process_id=AF-Process-de9223b1-a7c6-408f-aaa3-aee33fd7f7fa or at https://www.findmyaddress.co.uk/.

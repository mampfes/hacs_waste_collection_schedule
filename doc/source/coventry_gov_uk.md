# Coventry City Council

Support for schedules provided by [Coventry City Council](https://www.coventry.gov.uk/rubbishandrecycling), serving Coventry, UK.

The council retired its street directory. This source now reads the council's "Find my bin day" service by UPRN. Only the next collection date per bin type is available.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: coventry_gov_uk
      args:
        uprn: UPRN
```

### Configuration Variables
**uprn**  
*(string) (required)*<br>
Unique Property Reference Number of your address. You can find it at [findmyaddress.co.uk](https://www.findmyaddress.co.uk/).

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: coventry_gov_uk
      args:
        uprn: "100070666040"
```

# Fraser Coast Regional Council

Support for schedules provided by [Fraser Coast Regional Council](https://www.frasercoast.qld.gov.au).

Source for Fraser Coast Regional Council waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: frasercoast_qld_gov_au
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: frasercoast_qld_gov_au
      args:
        address: 57 Arbornine Road Glenwood
```

## How to get the source arguments

Enter your street address including suburb (e.g. '57 Arbornine Road Glenwood'). Search at https://www.frasercoast.qld.gov.au/Services/Online-Services/Check-your-bin-day

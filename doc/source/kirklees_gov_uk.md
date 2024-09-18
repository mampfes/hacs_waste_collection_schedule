# Kirklees Council

Support for schedules provided by [Kirklees Council](https://www.kirklees.gov.uk)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: kirklees_gov_uk
      args:
        door_num: 1
        postcode: "HD9 6RJ"
        uprn: UPRN # only required sometimes
```

### Configuration Variables

**door_num**  
*(string) (required)*

Door number identifier for the property

**postcode**  
*(string) (required)*

Postcode of the property

**uprn**  
*(string) (optional)*

Unique Property Reference Number (UPRN) of the property. This is required if multiple properties are found when searching by door number and postcode. An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.

## Example with UPRN

```yaml
waste_collection_schedule:
    sources:
    - name: kirklees_gov_uk
      args:
        door_num: 1
        postcode: "HD8 8NA"
        uprn: 83194785
```

# Australian Captial Territory (ACT)

Support for schedules provided by [ACT Goverment City Services](https://www.cityservices.act.gov.au/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: act_gov_au
      args:
        suburb: SUBURB
        split_Suburb: SPLIT SUBURB
```

### Configuration Variables

**suburb**  
*(string) (required)*

**split_suburb**  
*(string) (optional)*

## Examples

### Without split_suburb

```yaml
waste_collection_schedule:
  sources:
    - name: act_gov_au
      args:
        suburb: BRUCE
```

### With split_suburb

```yaml
waste_collection_schedule:
  sources:
    - name: act_gov_au
      args:
        suburb: DUNLOP
        split_Suburb: North
```

## How to get the source arguments

Visit the [ACT City Service's Bin Collection Calendar](https://www.cityservices.act.gov.au/recycling-and-waste/collection/bin-collection-calendar) page and look for your suburb. The suburb argument should be in all uppercase of what is found in the dropdown. Some suburbs like Charnwood and Dunlop have been split into multiple entries, to check if your suburb has been split go to the API: [https://www.data.act.gov.au/resource/jzzy-44un.json?suburb=SUBURB](https://www.data.act.gov.au/resource/jzzy-44un.json?suburb=SUBURB) and swap `SUBURB` for your suburb in uppercase, and check if more than one result is returned, if there is the `split_suburb` argument should be equal to `split_suburb` in your correct API result. For example Dunlop is split into north and south so the `split_suburb` argument would be equal to `North` or `South`.

# Belfast City Council

Support for schedules provided by [Belfast City Council](https://online.belfastcity.gov.uk/find-bin-collection-day).

Source for belfastcity.gov.uk waste collection services.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: belfast_city_gov_uk
      args:
        postcode: POSTCODE
        uprn: UPRN
```

### Configuration Variables

**postcode**  
*(string) (required)*

**uprn**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: belfast_city_gov_uk
      args:
        postcode: BT9 6DG
        uprn: '185075148'
```

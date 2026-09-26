# North Yorkshire Council - Richmondshire

Support for schedules provided by [North Yorkshire Council - Richmondshire](https://northyorks.gov.uk).

Source for North Yorkshire Council - Richmondshire.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: richmondshire_gov_uk
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
    - name: richmondshire_gov_uk
      args:
        uprn: 100050441864
```

## How to get the source arguments

Look your property up on the [North Yorkshire Council bin calendar](https://www.northyorks.gov.uk/bin-calendar/lookup). Your UPRN is the number at the end of the results page's URL, e.g. `https://www.northyorks.gov.uk/bin-calendar/Richmondshire/results/100050441864`.

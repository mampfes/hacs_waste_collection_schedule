# North Yorkshire Council - Scarborough

Support for schedules provided by [North Yorkshire Council - Scarborough](https://northyorks.gov.uk).

Source for North Yorkshire Council - Scarborough.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: northyorks_scarborough_gov_uk
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
    - name: northyorks_scarborough_gov_uk
      args:
        uprn: 100050497178
```

## How to get the source arguments

Look your property up on the [North Yorkshire Council bin calendar](https://www.northyorks.gov.uk/bin-calendar/lookup). Your UPRN is the number at the end of the results page's URL, e.g. `https://www.northyorks.gov.uk/bin-calendar/Scarborough/results/100050497178`.

# Stirling council Council

Support for schedules provided by [Stirling Council](https://www.stirling.gov.uk/), serving Stirlingshire, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    - name: stirling_uk
      args:
        route: "xxxx"
```

### Configuration Variables

**route**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: stirling_uk
      args:
        route: "9623"
```

### How to find your `Route`

Stirling council does not expose an easy API for bin collection. Hence this integration uses route number as opposed to traditional uprn

you can get the route number by visiting Stirling Council UK website and entering your address to check the url.

For example:   _stirling.gov.uk/bins-and-recycling/bin-collection-dates-search/collections/?route=`9748`

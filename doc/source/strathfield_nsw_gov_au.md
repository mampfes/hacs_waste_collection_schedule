# Strathfield Council

Support for schedules provided by [Strathfield Council](https://www.strathfield.nsw.gov.au).

Source for Strathfield Council, NSW, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: strathfield_nsw_gov_au
      args:
        collection_day: COLLECTION_DAY
```

### Configuration Variables

**collection_day**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: strathfield_nsw_gov_au
      args:
        collection_day: Monday
```

## How to get the source arguments

Enter the Monday-Friday collection day from your rates notice or the council's street guide. The current linked calendar supplies green/yellow weeks and actual dates. Dates stop at the published end instead of projecting a fixed anchor two years ahead. Types now use canonical, localised names; update filters and customisations using old labels.

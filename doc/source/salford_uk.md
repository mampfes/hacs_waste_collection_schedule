# Salford City Council

Support for schedules provided by [Salford City
Council](https://www.salford.gov.uk/bins-and-recycling/bin-collection-days/), serving the
city of Salford, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: salford_uk
      args:
        uprn: UPRN_CODE
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: salford_uk
      args:
        uprn: "100011404886"
```

## How to get the source argument

The UPRN code can be found by entering your postcode on the
[Salford City Council bin collections days page
](https://www.salford.gov.uk/bins-and-recycling/bin-collection-days/).  After selecting your address from the list and waiting for the new page to load, the uprn will be shown in the address bar.

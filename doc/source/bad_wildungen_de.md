# Stadt Bad Wildungen

Support for schedules provided by [Stadt Bad Wildungen](https://www.bad-wildungen.de).

Source for Stadt Bad Wildungen, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bad_wildungen_de
      args:
        street: STREET
```

### Configuration Variables

**street**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: bad_wildungen_de
      args:
        street: Reinhardshausen
```

## How to get the source arguments

Enter your street or, outside the core town, your Stadtteil (e.g. Reinhardshausen) as printed in the street directory of the city's waste calendar (Abfallkalender PDF on bad-wildungen.de). Where a street is split by house numbers, use the entry with the numbers, e.g. 'Königsquellenweg 12, 14, 16'.

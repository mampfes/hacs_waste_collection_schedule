# Castelnovetto, Candia Lomellina, Castello d'Agogna, Rosasco, Sant'Angelo Lomellina, Zeme

Support for schedules provided by [Castelnovetto, Candia Lomellina, Castello d'Agogna, Rosasco, Sant'Angelo Lomellina, Zeme](https://www.comune.castelnovetto.pv.it).

Source for the shared door-to-door collection calendar of Castelnovetto and five neighbouring comuni (Lomellina, Pavia).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: castelnovetto_pv_it
```

### Configuration Variables

No configuration arguments are required.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: castelnovetto_pv_it
```

## How to get the source arguments

No configuration is needed: Candia Lomellina, Castello d'Agogna, Castelnovetto, Rosasco, Sant'Angelo Lomellina and Zeme share one calendar, read from the yearly notice on Castelnovetto's website.

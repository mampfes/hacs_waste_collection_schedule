# Town of Victoria Park

Support for schedules provided by [Town of Victoria Park](https://www.victoriapark.wa.gov.au).

Source for www.victoriapark.wa.gov.au Waste Collection Services

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: victoriapark_wa_gov_au
      args:
        group: GROUP
        day: DAY
```

### Configuration Variables

**group**  
*(string) (optional)*

**day**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: victoriapark_wa_gov_au
      args:
        group: 1
        day: Monday
```

## How to get the source arguments

Find your collection group (1 or 2) and weekday on the council Bins and Collections page. The current linked July-June image calendar supplies the actual red/yellow weeks and public-holiday replacement dates. Dates stop at its published end; no fixed historical anchor is used. Since the v3 pipeline migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels.

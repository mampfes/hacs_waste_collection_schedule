# Town of Victoria Park

```yaml
waste_collection_schedule:
  sources:
    - name: victoriapark_wa_gov_au
      args:
        group: 1
        day: "Monday"
```

Find your collection group (1 or 2) and weekday on the [Bins and Collections page](https://www.victoriapark.wa.gov.au/residents/waste-and-recycling/bins-and-collections.aspx).

- `group`: Collection group, 1 or 2.
- `day`: Collection weekday, Monday to Friday.

The source discovers the current group calendar image and reads the dated red/yellow week cells. FOGO is weekly; general waste and recycling alternate as printed. Green holiday cells use the following day's printed replacement. Dates stop at the end of the published July-June guide. An expired or incomplete calendar raises an error; there is no projection from a historical anchor.

## BaseSource migration

Configuration argument names stay unchanged. Waste types now use canonical, localised names; update filters, automations and customisations using the former labels.

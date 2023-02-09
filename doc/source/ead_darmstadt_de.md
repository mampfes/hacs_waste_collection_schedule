# KWU Entsorgung

Support for schedules provided by [ead.darmstadt.de](https://ead.darmstadt.de/) serving the city of Darmstadt, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ead_darmstadt_de
      args:
        street: Achatweg
```

### Configuration Variables

**street**  
*(string) (required)*

## How to get the source arguments

Visit [Abfallkalender](https://ead.darmstadt.de/unser-angebot/privathaushalte/abfallkalender/`) and search for your address. The `street` argument should exactly match the autocomplete result and may contain a number or range as well.

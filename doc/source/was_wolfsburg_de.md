# Wolfsburger Abfallwirtschaft und Straßenreinigung

Support for schedules provided by [WAS-Wolfsburg.de](https://was-wolfsburg.de).

Please note that WAS Wolfsburg provides 2 different schedules: One for "Restabfall - Bioabfall - Altpapier" and one for "Gelber Sack". This source fetches both schedules and merges it into one.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: was_wolfsburg_de
      args:
        city: CITY
        street: STREET
```

### Configuration Variables

**city**<br>
*(string) (required)*

**street**<br>
*(string) (required)*


## Example

```yaml
waste_collection_schedule:
  sources:
    - name: was_wolfsburg_de
      args:
        city: Barnstorf
        street: Bahnhofspassage
```

## How to get the source arguments

| Argument | Description |
| ----------- | ----------- |
| city | Full district name as shown in the `Gelber Sack` web page. |
| street | Full street name as shown in the `Restabfall/Bioabfall/Altpapier` web page. |
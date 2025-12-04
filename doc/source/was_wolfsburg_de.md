# Wolfsburger Abfallwirtschaft und Straßenreinigung

Support for schedules provided by [WAS-Wolfsburg.de](https://was-wolfsburg.de).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: was_wolfsburg_de
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
    - name: was_wolfsburg_de
      args:
        street: Bahnhofspassage
```

## How to get the source arguments

| Argument | Description |
| ----------- | ----------- |
| street | Full street name as shown in the `Restabfall/Bioabfall/Altpapier` web page. (can be left out if you ONLY want to fetch `Gelber Sack`) |

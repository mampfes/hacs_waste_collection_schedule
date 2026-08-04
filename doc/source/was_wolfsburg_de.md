# Wolfsburger Abfallwirtschaft und Straßenreinigung

Support for schedules provided by [WAS-Wolfsburg.de](https://was-wolfsburg.de).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: was_wolfsburg_de
      args:
        street: STREET
        number: HOUSE_NUMBER
```

### Configuration Variables

**street**  
*(string) (required)*

**number**  
*(integer) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: was_wolfsburg_de
      args:
        street: Bahnhofspassage
        number: 1
```

## How to get the source arguments

| Argument | Description |
| ----------- | ----------- |
| street | Full street name as shown in the WAS web app. |
| number | House number as shown in the WAS web app. |

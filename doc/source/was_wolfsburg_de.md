# Wolfsburger Abfallwirtschaft und Straßenreinigung

Support for schedules provided by [Wolfsburger Abfallwirtschaft und Straßenreinigung](https://was-wolfsburg.de).

Source for waste collections for WAS-Wolfsburg, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: was_wolfsburg_de
      args:
        street: STREET
        number: NUMBER
```

### Configuration Variables

**street**  
*(string) (required)*

**number**  
*(string) (required)*

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

Enter the street name and house number exactly as listed on https://abfuhrtermine.waswob.de/.

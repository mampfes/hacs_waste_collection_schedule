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

Open [abfuhrtermine.waswob.de](https://abfuhrtermine.waswob.de/) and select your address. Use exactly the street name and house number offered there.

| Argument | Description |
| ----------- | ----------- |
| street | Full street name as listed on [abfuhrtermine.waswob.de](https://abfuhrtermine.waswob.de/), e.g. `Bärheide`. |
| number | House number as listed on [abfuhrtermine.waswob.de](https://abfuhrtermine.waswob.de/), e.g. `1`. |

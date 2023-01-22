# Linköping - Tekniska Verken

Support for schedules provided by [Linköping - Tekniska Verken](https://www.tekniskaverken.se/privat/avfall-och-atervinning/mat-och-restavfall/), serving the municipalities of Linköping, Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: tekniskaverken_se
      args:
        street: STREET_NAME
        city: CITY_NAME
```

### Configuration Variables

**street**
*(string) (required)*

**city**
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: tekniskaverken_se
      args:
        street: Brigadgatan 4
        city: Linköping
```

## How to get the source argument

The source argument is the street including number and the city to the house with waste collection. 
The address can be tested [here]((https://www.tekniskaverken.se/privat/avfall-och-atervinning/mat-och-restavfall/).
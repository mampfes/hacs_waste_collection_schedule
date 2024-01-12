# Gästrike Återvinnare

Support for schedules provided by [Gästrike Återvinnare](https://gastrikeatervinnare.se/privat/hamtningsdag/), serving the region of Gästrikland, Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gastrikeatervinnare_se
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
        street: Bryggargatan 6
        city: Sandviken
```

## How to get the source argument

The source argument is the street including number and the city to the house with waste collection.
The address can be tested [here](https://gastrikeatervinnare.se/privat/hamtningsdag/).
Note that the city can't be used in the search above, and is only used as a differentiator in case several citys have the same street adress.

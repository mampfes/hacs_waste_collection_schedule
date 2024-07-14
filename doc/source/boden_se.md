# Boden Avfall och Återbruk Sophämtning

Support for schedules provided by [Boden](https://www.boden.se/boende-trafik/avfall-och-aterbruk/avfall-395A), serving the municipality of Boden, Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: boden_se
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: boden_se
      args:
        street_address: KYRKGATAN 24, Boden
```

## How to get the source argument

The source argument is the address to the house with waste collection. You can try it by entering your address in the search field here [here](https://www.boden.se/boende-trafik/avfall-och-aterbruk/avfall-395A).

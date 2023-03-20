# VA Syd Sophämntning

Support for schedules provided by [VA Syd](https://www.vasyd.se/Artiklar/Avfall-och-soptomning-privat/sopt%C3%B6mning-schema/), serving the municipality of Malmö, Lund, Lomma, Eslöv and Burlöv, Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: vasyd_se
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
    - name: vasyd_se
      args:
        street_address: Industrigatan 13, Malmö
```

## How to get the source argument

The source argument is the address to the house with waste collection. The address can be tested [here](https://www.vasyd.se/Artiklar/Avfall-och-soptomning-privat/sopt%C3%B6mning-schema/).

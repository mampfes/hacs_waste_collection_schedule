# Sysav Sophämtning

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

**street_address**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: vasyd_se
      args:
        street_address: Industrigatan 13, Malmö
      customize:
        - type: Fyrfack1
          alias: Brännbart, kompost, plast & färgat glas
        - type: Fyrfack2
          alias: Pappersförpackningar, tidningar, metall & ofärgat glas

sensors:
  - platform: waste_collection_schedule
    name: next_yard_collection
    types:
      - Trädgårdsavfall
  - platform: waste_collection_schedule
    name: next_bin1_collection
    types:
      - Brännbart, kompost, plast & färgat glas
  - platform: waste_collection_schedule
    name: next_bin2_collection
    types:
      - Pappersförpackningar, tidningar, metall & ofärgat glas
```

## How to get the source argument

The source argument is the address to the house with waste collection. The address can be tested [here](https://www.vasyd.se/Artiklar/Avfall-och-soptomning-privat/sopt%C3%B6mning-schema/).

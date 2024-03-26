# Kristianstad Renhållning Sophämntning

Support for schedules provided by [Kristianstad Renhållning](https://renhallningen-kristianstad.se/villa-fritidshus/tomning-av-sopkarl/tomningschema/), serving the municipality of Kristianstad Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: krab_se
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
    - name: krab_se
      args:
        street_address: Östra Boulevarden 1
```

## How to get the source argument

The source argument is the address to the house with waste collection. The address can be tested [here](https://renhallningen-kristianstad.se/villa-fritidshus/tomning-av-sopkarl/tomningschema/).

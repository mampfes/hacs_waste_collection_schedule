# Sysav Sophämtning

Support for schedules provided by [Sysav](https://www.sysav.se/Privat/min-sophamtning/), serving the municipality of Svedala, Kävlinge and Lomma, Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sysav_se
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
    - name: sysav_se
      args:
        street_address: Sommargatan 1, Svedala
```

## How to get the source argument

The source argument is the address to the house with waste collection. The address can be tested [here](https://www.sysav.se/Privat/min-sophamtning/).

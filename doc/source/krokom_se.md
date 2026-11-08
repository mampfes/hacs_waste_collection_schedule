# Krokom

Support for schedules provided by [Krokom](https://krokom.se/bo-trafik-och-miljo/avfall-och-atervinning/avfallshamtning.html).

Waste collection schedule for Krokom Municipality, Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: krokom_se
      args:
        address: ADDRESS
        city: CITY
```

### Configuration Variables

**address**  
*(string) (required)*

**city**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: krokom_se
      args:
        address: Bergfinkvägen 3
        city: Ås
```

## How to get the source arguments

Enter your street and house number as shown by the 'När kommer sopbilen?' search on the [Krokom waste page](https://krokom.se/bo-trafik-och-miljo/avfall-och-atervinning/avfallshamtning.html), e.g. `Offerdalsvägen 1`. If the same street name exists in several towns, also enter the town (e.g. `Föllinge`). The service only publishes the next collection date.

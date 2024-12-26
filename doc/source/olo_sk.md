# fcc Environment (VYLOŽ SMETI APP)

Support for schedules provided by [OLO Bratislava](https://www.olo.sk/), serving in Bratislava in Slovakia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: olo_sk
      args:
        street: STREET

```

### Configuration Variables

**street**
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: olo_sk
      args:
        street: Jantarova 47
```

```yaml
waste_collection_schedule:
    sources:
    - name: olo_sk
      args:
        city: Jasovska 8
```
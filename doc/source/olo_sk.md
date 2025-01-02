Support for schedules provided by [OLO](https://www.olo.sk/), serving in Bratislava, Slovakia.
These waste types are supported:
- Zmesovy odpad
- Triedeny odpad
- Kuchynsky odpad

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: olo_sk
      args:
        street: STREET
        registrationNumber: NUMBER

```

### Configuration Variables

**street**
*(String) (required)*

**registrationNumber**
*(String) (optional)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: olo_sk
      args:
        street: Jantarova 47
        registrationNumber: 123456
```

```yaml
waste_collection_schedule:
    sources:
    - name: olo_sk
      args:
        street: Jasovska 8
        registrationNumber: 987654
```
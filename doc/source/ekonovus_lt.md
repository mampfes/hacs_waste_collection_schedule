# Ekonovus

Support for schedules provided by [Ekonovus](https://www.ekonovus.lt).

Source for UAB "Ekonovus" waste collection schedule.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ekonovus_lt
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ekonovus_lt
      args:
        address: Margirio g. 16
```

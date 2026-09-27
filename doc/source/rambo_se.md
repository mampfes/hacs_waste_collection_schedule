# North / Middle Bohuslän - Rambo AB

Support for schedules provided by [North / Middle Bohuslän - Rambo AB](https://www.rambo.se/).

Source for North / Middle Bohuslän - Rambo AB.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: rambo_se
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
    - name: rambo_se
      args:
        address: "Grebbestad \xD6.l\xE5nggat./Storg., Grebbestad"
```

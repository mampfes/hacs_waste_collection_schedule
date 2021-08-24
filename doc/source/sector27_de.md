# sector27.de

Support for schedules provided by [Sector27.de](https://muellkalender.sector27.de). Some cities use this service, e.g. Datteln, Oer-Erkenschwick and Marl.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sector27_de
      args:
        city: CITY
        street: STREET
```

### Configuration Variables

**CITY**<br>
*(string) (required)*

**STREET**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: sector27_de
      args:
        city: Marl
        street: Ahornweg
```

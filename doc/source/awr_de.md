# AWR

Support for schedules provided by [AWR](https://www.awr.de)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: awr_de
      args:
        city: CITY
        street: STREET
```
### Configuration Variables

**city**<br>
*(string) (required)*

**street**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: awr_de
      args:
        city: Rendsburg
        street: Hindenburgstraße
```

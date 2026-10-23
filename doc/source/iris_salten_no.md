# Iris Salten

Support for schedules provided by [Iris Salten](https://www.iris-salten.no).

Fetches waste collection schedule from Iris Salten (based on address).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: iris_salten_no
      args:
        address: ADDRESS
        kommune: KOMMUNE
```

### Configuration Variables

**address**  
*(string) (required)*

**kommune**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: iris_salten_no
      args:
        address: "Alsosg\xE5rden 11"
        kommune: "Bod\xF8 kommune"
```

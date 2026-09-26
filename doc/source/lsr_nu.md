# Landskrona - Svalövs Renhållning

Support for schedules provided by [Landskrona - Svalövs Renhållning](https://www.lsr.nu).

Source for LSR waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: lsr_nu
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
    - name: lsr_nu
      args:
        street_address: "Saxtorpsv\xE4gen 115, Annel\xF6v"
```

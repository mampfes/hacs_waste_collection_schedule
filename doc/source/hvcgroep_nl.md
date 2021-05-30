# HVCGroep

Support for schedules provided by [hvcgroep.nl](https://www.hvcgroep.nl/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hvcgroep_nl
      args:
        postal_code: POSTAL_CODE
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**postal_code**<br>
*(string) (required)*

**house_number**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: hvcgroep_nl
      args:
        postal_code: 1713VM
        house_number: 1
```

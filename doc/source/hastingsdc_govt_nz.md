# Hastings District Council

Support for schedules provided by [Hastings District Council](https://www.hastingsdc.govt.nz/).

Source for Napier City Council

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hastingsdc_govt_nz
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
    - name: hastingsdc_govt_nz
      args:
        address: 805 Fitzroy Avenue
```

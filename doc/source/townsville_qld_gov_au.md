# Townsville

Support for schedules provided by [Townsville](https://townsville.qld.gov.au/).

Source for Townsville.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: townsville_qld_gov_au
      args:
        property_id: PROPERTY_ID
```

### Configuration Variables

**property_id**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: townsville_qld_gov_au
      args:
        property_id: 009fe2d01b9ba090598520202d4bcbc7
```

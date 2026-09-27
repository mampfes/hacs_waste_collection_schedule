# North Kesteven District Council

Support for schedules provided by [North Kesteven District Council](https://n-kesteven.org.uk).

Source for n-kesteven.org.uk services for North Kesteven District Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: north_kesteven_org_uk
      args:
        uprn: UPRN
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: north_kesteven_org_uk
      args:
        uprn: '100030860713'
```

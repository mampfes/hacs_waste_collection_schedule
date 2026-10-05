# Wiltshire Council

Support for schedules provided by [Wiltshire Council](https://wiltshire.gov.uk).

Source for wiltshire.gov.uk services for Wiltshire Council

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: wiltshire_gov_uk
      args:
        uprn: UPRN
        postcode: POSTCODE
```

### Configuration Variables

**uprn**  
*(string) (required)*

**postcode**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: wiltshire_gov_uk
      args:
        uprn: '100121085972'
        postcode: BA149QP
```

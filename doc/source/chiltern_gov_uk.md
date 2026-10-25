# Deprecated: Buckinghamshire

Support for schedules provided by [Deprecated: Buckinghamshire](https://chiltern.gov.uk).

Deprecated: use the iapp_iTouchVision instead.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: chiltern_gov_uk
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
    - name: chiltern_gov_uk
      args:
        uprn: 766251559
```

## How to get the source arguments

Deprecated. Add iTouchVision instead and choose municipality BUCKINGHAMSHIRE. This entry still accepts a UPRN and reads the Buckinghamshire bin-day form.

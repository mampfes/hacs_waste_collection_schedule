# Matamata-Piako District Council

Support for schedules provided by [Matamata-Piako District Council](https://www.mpdc.govt.nz/calendar).

Source for Matamata-Piako District Council kerbside collections.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mpdc_govt_nz
      args:
        area: AREA
```

### Configuration Variables

**area**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: mpdc_govt_nz
      args:
        area: Matamata, Waharoa, Walton and Tamihana
```

## How to get the source arguments

Visit https://www.mpdc.govt.nz/calendar and select the rubbish and recycling group containing your town.

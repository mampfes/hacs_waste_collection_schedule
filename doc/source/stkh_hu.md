# STKH Sopron és Térsége

Support for schedules provided by [STKH Sopron és Térsége](https://www.stkh.hu).

Waste collection schedule for municipalities served by STKH (Sopron és Térsége), Hungary, published as a per-municipality PDF.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: stkh_hu
      args:
        url: URL
```

### Configuration Variables

**url**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: stkh_hu
      args:
        url: https://stkh.hu/wp-content/uploads/2025/12/9472_Ujker_Hulladeknaptar2026.pdf
```

## How to get the source arguments

Find your municipality's waste calendar (hulladéknaptár) PDF on https://www.stkh.hu (Szolgáltatásaink), then enter the direct PDF link as the 'Calendar PDF URL' value.

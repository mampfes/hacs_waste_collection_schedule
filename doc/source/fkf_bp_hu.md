# FKF Budapest

Support for schedules provided by [FKF Budapest](https://www.fkf.hu/hulladeknaptar), serving Budapest, HU.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: fkf_bp_hu
      args:
        district: AREA_CODE
        street: FULL_STREET_NAME
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**DISTRICT**
*(number) (required)*
4 digits (e.g. 1011)

**STREET**
*(string) (required)*

**HOUSE_NUMBER**
*(number) (required)*


## Example

```yaml
waste_collection_schedule:
    sources:
    - name: fkf_bp_hu
      args:
        district: 1011
        street: "Apród utca"
        house_number: 10
```
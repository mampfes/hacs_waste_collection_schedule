# FKF Budaörs

Support for schedules provided by [FKF Budaörs](https://www.fkf.hu/hulladeknaptar-budaors), serving Budaörs, HU.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: fkf_bo_hu
      args:
        street: FULL_STREET_NAME
```

### Configuration Variables

**STREET**
*(string) (required)*


## Example

```yaml
waste_collection_schedule:
    sources:
    - name: allerdale_gov_uk
      args:
        street: "Templom tér"
```
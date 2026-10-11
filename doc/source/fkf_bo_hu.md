# FKF Budaörs

Support for schedules provided by [FKF Budaörs](https://www.fkf.hu).

Source script for www.fkf.hu

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: fkf_bo_hu
      args:
        street: STREET
        ssl_verify: SSL_VERIFY
```

### Configuration Variables

**street**  
*(string) (required)*

**ssl_verify**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: fkf_bo_hu
      args:
        street: "Templom t\xE9r"
```

## How to get the source arguments

Enter the street as the calendar's street list at https://www.mohubudapest.hu/hulladeknaptar-budaors writes it. `ssl_verify` is no longer used.

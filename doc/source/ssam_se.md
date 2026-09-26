# SSAM (Deprecated)

Support for schedules provided by [SSAM (Deprecated)](https://ssam.se).

Deprecated, please use edpevent_se instead.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ssam_se
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ssam_se
      args:
        street_address: "Asteroidv\xE4gen 1, V\xE4xj\xF6"
```

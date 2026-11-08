# Uppsala Vatten och Avfall AB (Deprecated)

Support for schedules provided by [Uppsala Vatten och Avfall AB (Deprecated)](https://www.uppsalavatten.se).

Deprecated, please use edpevent_se instead.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: uppsalavatten_se
      args:
        street: STREET
        city: CITY
```

### Configuration Variables

**street**  
*(string) (required)*

**city**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: uppsalavatten_se
      args:
        city: BJÖRKLINGE
        street: SADELVÄGEN 1
```

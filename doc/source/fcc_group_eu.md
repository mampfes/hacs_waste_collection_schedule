# fcc Environment

Support for schedules provided by [fcc Environment](https://www.fcc-group.eu/).

Source for fcc Environment.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: fcc_group_eu
      args:
        city: CITY
        location: LOCATION
        frequency: FREQUENCY
```

### Configuration Variables

**city**  
*(string) (required)*

**location**  
*(string) (optional)*

**frequency**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: fcc_group_eu
      args:
        city: "C\xEDfer"
        location: "J. Kub\xE1nyiho"
```

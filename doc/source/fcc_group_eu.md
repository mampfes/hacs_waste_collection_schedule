# fcc Environment (VYLOŽ SMETI APP)

Support for schedules provided by [fcc Environment](https://www.fcc-group.eu/), serving multiple municipalities in Slovakia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: fcc_group_eu
      args:
        city: CITY
        location: LOCATION
        
```

### Configuration Variables

**city**  
*(String) (required)*

**location**  
*(String) (optional)* Not all cities require this argument.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: fcc_group_eu
      args:
        city: Cífer
        location: J. Kubányiho
```

```yaml
waste_collection_schedule:
    sources:
    - name: fcc_group_eu
      args:
        city: Borinka
```

## How to get the source argument

The source uses the API of the VYLOŽ SMETI APP, so the arguments should match the ones in the app.

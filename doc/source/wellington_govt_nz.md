# Wellington City Council

Support for schedules provided by [Wellington City Council](https://wellington.govt.nz).

Source for Wellington City Council.

## Configuration via configuration.yaml

### Using streetId

```yaml
waste_collection_schedule:
  sources:
    - name: wellington_govt_nz
      args:
        streetId: STREETID
```

### Using streetName

```yaml
waste_collection_schedule:
  sources:
    - name: wellington_govt_nz
      args:
        streetName: STREETNAME
```

### Configuration Variables

**streetId**  
*(string) (alternative)*

**streetName**  
*(string) (alternative)*

Provide one of: `streetId` or `streetName`.

## Example

### Using streetId

```yaml
waste_collection_schedule:
  sources:
    - name: wellington_govt_nz
      args:
        streetId: '6515'
```

### Using streetName

```yaml
waste_collection_schedule:
  sources:
    - name: wellington_govt_nz
      args:
        streetName: Cheltenham Terrace
```

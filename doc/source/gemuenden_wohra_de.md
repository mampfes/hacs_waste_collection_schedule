# Stadt Gemünden (Wohra)

Support for schedules provided by [Stadt Gemünden (Wohra)](https://www.gemuenden-wohra.de), serving Gemünden (Wohra), Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gemuenden_wohra_de
      args:
        tour: 1
```

### Configuration Variables

**tour**
*(integer) (required)*

Collection tour number. Determines which pickup route your address belongs to:

- **Tour 1**: Schiffelbach, Ellnrode, Grüsen, Sehlen, Herbelhausen, Lehnhausen and all properties west of the former railway line.
- **Tour 2**: Rest of Gemünden town centre.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: gemuenden_wohra_de
      args:
        tour: 2
```

## Collected waste types

| Code | Type | Description |
|------|------|-------------|
| B | Bioabfall | Organic waste |
| R | Restmüll | Residual waste |
| G | Gelbe Tonne | Yellow bin (packaging) |
| P | Altpapier | Paper |
| AR | Altreifensammlung | Old tyre collection (all tours) |
| SO | Sonderabfall | Hazardous waste collection (all tours) |

# Appfuhr.de Ammerland

Support for schedules provided by [Appfuhr.de](https://www.awb-ammerland.de), serving Landkreis Ammerland, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: appfuhr_de
      args:
        strid: STRID
```

### Configuration Variables

**strid**
*(integer) (required)*
Identifier of the street or street section as used in the Appfuhr data.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: appfuhr_de
      args:
        strid: 123
```

## How to get the source argument

The `strid` can be extracted from the JSON file used by the official Appfuhr.de mobile app. Search for the `strid` value that matches your street or section.

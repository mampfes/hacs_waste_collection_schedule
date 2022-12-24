# Cochem-Zell

Support for schedules provided by <https://www.cochem-zell-online.de/abfallkalender/>.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cochem_zell_online_de
      args:
        district: DISTRICT
```

### Configuration Variables

**district**  
_(string) (required)_

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: cochem_zell_online_de
      args:
        district: "Zell-Stadt"
```

## How to get the source arguments

1. Open <https://www.cochem-zell-online.de/abfallkalender/>.
2. Click on the selection field named `Ortsteil`.
3. Enter the name _with correct capitalization_ in the argument `district`.

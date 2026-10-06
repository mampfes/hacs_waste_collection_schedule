# HRA (Hadeland og Ringerike Avfallsselskap)

Support for schedules provided by [HRA (Hadeland og Ringerike Avfallsselskap)](https://hra.no).

Source for HRA waste collection in Hadeland (Gran, Jevnaker, Lunner), Norway.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hra_no
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: hra_no
      args:
        address: Myllavegen 1, 2742 GRUA
```

## How to get the source arguments

Search for your address at hra.no/tommekalender and use the address as shown in the result list, e.g. 'Myllavegen 1, 2742 GRUA'.

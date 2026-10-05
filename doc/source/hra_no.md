# HRA (Hadeland og Ringerike Avfallsselskap)

Support for schedules provided by [HRA](https://hra.no), serving the Hadeland region (Gran, Jevnaker, Lunner), Norway.

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
*(String) (required)*

The address as shown in the search result on the HRA collection calendar, for example `Myllavegen 1, 2742 GRUA`. The postal code and place may be omitted if the street address is unique.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: hra_no
      args:
        address: Myllavegen 1, 2742 GRUA
```

## How to get the source argument

Visit [https://hra.no/tommekalender](https://hra.no/tommekalender), search for your address, and use it exactly as shown in the result list.

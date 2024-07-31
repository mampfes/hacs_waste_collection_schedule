# Fosen Renovasjon

Support for schedules provided by [Fosen Renovasjon](https://fosenrenovasjon.no/), serving Fosen, Norway.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: fosenrenovasjon_no
      args:
        address: ADDRESS
        
```

### Configuration Variables

**address**  
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: fosenrenovasjon_no
      args:
        address: Lysøysundveien 117
        
```

## How to get the source argument

Visit <https://fosenrenovasjon.no/tommekalender/#!/main> and search for your address, then use the address spelled exactly as the autocomplete suggests.

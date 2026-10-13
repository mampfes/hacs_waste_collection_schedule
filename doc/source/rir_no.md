# RIR

Support for schedules provided by [RIR](https://www.rir.no).

Source for RIR (Romsdalshalvøya Interkommunale Renovasjonsselskap), serving the municipalities of Aukra, Hustadvika, Gjemnes, Molde and Rauma, Norway.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: rir_no
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
    - name: rir_no
      args:
        address: "\xD8vre veg 10C, Molde"
```

## How to get the source arguments

Visit https://www.rir.no/hentekalender, start typing your address in the search field, and copy the suggested address exactly (including the postal town) into the 'address' argument.

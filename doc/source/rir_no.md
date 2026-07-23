# RIR

Support for schedules provided by [RIR (Romsdalshalvøya Interkommunale Renovasjonsselskap)](https://www.rir.no), serving the municipalities of Aukra, Hustadvika, Gjemnes, Molde and Rauma, Norway.

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
*(String) (required)*

The full address, exactly as suggested by the address search on rir.no/hentekalender.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: rir_no
      args:
        address: Øvre veg 10C, Molde
```

## How to get the source argument

Visit [https://www.rir.no/hentekalender](https://www.rir.no/hentekalender), start typing your address in the search field, and copy the suggested address exactly (including the postal town) into the `address` argument.

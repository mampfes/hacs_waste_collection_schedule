# BIR (Bergensområdets Interkommunale Renovasjonsselskap)

Support for schedules provided by [BIR (Bergensområdets Interkommunale Renovasjonsselskap)](https://bir.no).

Askøy, Bergen, Bjørnafjorden, Eidfjord, Kvam, Osterøy, Samnanger, Ulvik, Vaksdal, Øygarden og Voss Kommune (Norway).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bir_no
      args:
        street_name: STREET_NAME
        house_number: HOUSE_NUMBER
        house_letter: HOUSE_LETTER
```

### Configuration Variables

**street_name**  
*(string) (required)*

**house_number**  
*(string) (required)*

**house_letter**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: bir_no
      args:
        street_name: "Nord\xE5sgrenda"
        house_number: 7
        house_letter: ''
```

## How to get the source arguments

Enter the street name and the house number as written on bir.no/adressesoek. A house letter can be given in its own field or as part of the house number (for example 13B).

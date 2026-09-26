# Clackmannanshire Council

Support for schedules provided by [Clackmannanshire Council](https://www.clacks.gov.uk).

Source for Clackmannanshire Council, UK waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: clackmannanshire_gov_uk
      args:
        postcode: POSTCODE
        address: ADDRESS
        garden_waste: GARDEN_WASTE
```

### Configuration Variables

**postcode**  
*(string) (required)*

**address**  
*(string) (required)*

**garden_waste**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: clackmannanshire_gov_uk
      args:
        postcode: FK10 3EY
        address: 16 Crophill, Sauchie
```

## How to get the source arguments

Enter your postcode, e.g. 'FK10 3EY', and the address exactly as shown in the search results on the council website, e.g. '16 Crophill, Sauchie'. Set garden waste to true if you hold a paid garden waste (brown bin) permit, to include its collection dates.

# Frankston City Council

Waste collection schedules provided by [Frankston City Council](https://www.frankston.vic.gov.au/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: frankston_vic_gov_au
      args:
        address: ADDRESS # Formatting should be precise, please see below
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: frankston_vic_gov_au
      args:
        address: 45r Wedge Rd, Carrum Downs Vic
```

## How to get the correct address

For best results, search your address on [Frankston City Council's Website](https://www.frankston.vic.gov.au/My-Property/Waste-and-recycling/My-bins/Bin-collections) to ensure you use the correct address format. Start typing the full address and the use autocomplete to search. After results have been found, copy the address exactly as it appears in the search box.

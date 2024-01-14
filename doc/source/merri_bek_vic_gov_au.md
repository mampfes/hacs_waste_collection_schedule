# Merri-bek City Council (VIC)

Support for schedules provided by [Merri-bek City Council (VIC)](https://www.merri-bek.vic.gov.au/living-in-merri-bek/waste-and-recycling/bins-and-collection-services/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: merri_bek_vic_gov_au
      args:
        address: address
```

### Configuration Variables

**address**
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: merri_bek_vic_gov_au
      args:
        address: 90 Bell Street Coburg 3058
```

## How to get the source arguments

Search your address on [Merri-bek City Council's Website](https://www.merri-bek.vic.gov.au/living-in-merri-bek/waste-and-recycling/bins-and-collection-services/) to ensure you use the correct address format. Start typing the full address and the use autocomplete to search. After results have been found, copy the address exactly as it appears in the search box.

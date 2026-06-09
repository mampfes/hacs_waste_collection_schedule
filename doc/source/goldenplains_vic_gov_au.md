# Golden Plains Shire Council

Waste collection schedules provided by [Golden Plains Shire Council](https://www.goldenplains.vic.gov.au/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: goldenplains_vic_gov_au
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
    - name: goldenplains_vic_gov_au
      args:
        address: 2 POPE STREET BANNOCKBURN 3331
```

## How to get the correct address

Search your address on the [Golden Plains Shire Council waste collection page](https://www.goldenplains.vic.gov.au/address-search) and use the address exactly as it appears in the autocomplete suggestions (typically in the format `STREET NUMBER STREET NAME SUBURB POSTCODE`).

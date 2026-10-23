# SUM Avfall (Sunnfjord og Ytre Sogn Miljøverk IKS)

Support for schedules provided by [SUM Avfall (Sunnfjord og Ytre Sogn Miljøverk IKS)](https://www.sumavfall.no).

Source script for sumavfall.no - Sunnfjord og Ytre Sogn Miljøverk IKS

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sumavfall_no
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
    - name: sumavfall_no
      args:
        address: "bl\xE5b\xE6rlia-16"
```

## How to get the source arguments

The address slug as it appears in the calendar URL (`https://www.sumavfall.no/tommekalender?adresse=...`), e.g. 'blåbærlia-16' or 'storgata-1'.

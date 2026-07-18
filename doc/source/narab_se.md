# Nårab - Norra Åsbo Renhållnings AB

Support for schedules provided by [Nårab - Norra Åsbo Renhållnings AB](https://narab.se).

Source script for narab.se

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: narab_se
      args:
        address: ADDRESS
        kundNr: KUNDNR
```

### Configuration Variables

**address**  
*(string) (required)*

**kundNr**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: narab_se
      args:
        address: "Helsingborgsv\xE4gen 31"
        kundNr: 25494
```

## How to get the source arguments

Enter your address. If more than one collection shares the address, also provide your customer number (kundNr). Fetch your calendar at narabtomningskalender.se and run narabKUNDNRData.value in the browser console to read it.

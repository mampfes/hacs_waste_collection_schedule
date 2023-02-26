# Hume City Council

Waste collection schedules provided by [Hume City Council](https://www.hume.vic.gov.au).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hume_vic_gov_au
      args:
        address: ADDRESS # FORMATTING MUST BE EXACT, PLEASE SEE BELOW
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: hume_vic_gov_au
      args:
        address: 280 SOMERTON ROAD ROXBURGH PARK  VIC  3064
```

## How to get the correct address

Search your address on [Hume City Council Know My Bin Day](https://maps.hume.vic.gov.au/IntraMaps98/ApplicationEngine/frontend/mapbuilder/default.htm?configId=00000000-0000-0000-0000-000000000000&liteConfigId=a0ca08ad-7531-4cf3-b653-5d2533d007f0&title=SHVtZSBDaXR5IENvdW5jaWwgTmVhck1l) to ensure you use the correct address format. Leave out commas and include both "VIC" and your postcode.
# Town of Bassendean

Support for schedules provided by [Town of Bassendean](https://www.bassendean.wa.gov.au/environment-waste/recycling-waste).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bassendean_wa_gov_au
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
    - name: bassendean_wa_gov_au
      args:
        address: 16 Kenny St, Bassendean
```

## How to get the source arguments

Visit the [Town of Bassendean Find My Bin Day](https://bassendean.maps.arcgis.com/apps/instant/lookup/index.html?appid=95c3e8687b9f42b9b4b7757dd43efac3) page and search for your address. The address should match the format used in the lookup, e.g. "16 Kenny St, Bassendean".

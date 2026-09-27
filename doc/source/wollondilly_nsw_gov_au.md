# Wollondilly Shire Council

Support for schedules provided by [Wollondilly Shire Council](https://www.wollondilly.nsw.gov.au/).

Source for Wollondilly Shire Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: wollondilly_nsw_gov_au
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
    - name: wollondilly_nsw_gov_au
      args:
        address: 87 Remembrance Driveway TAHMOOR NSW
```

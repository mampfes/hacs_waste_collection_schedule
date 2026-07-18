# City of Kwinana

Support for schedules provided by [City of Kwinana](https://www.kwinana.wa.gov.au).

Source for City of Kwinana waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kwinana_wa_gov_au
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
    - name: kwinana_wa_gov_au
      args:
        address: 1 Chisham Avenue KWINANA TOWN CENTRE
```

## How to get the source arguments

Enter your street address including suburb (e.g. '25 Breccia Parade WELLARD').

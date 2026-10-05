# Cardinia Shire Council

Support for schedules provided by [Cardinia Shire Council](https://www.cardinia.vic.gov.au).

Source script for cardinia.vic.gov.au

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cardinia_vic_gov_au
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
    - name: cardinia_vic_gov_au
      args:
        address: 1015 Manks Rd, Dalmore Vic
```

## How to get the source arguments

Enter your street address including suburb (e.g. '124 Main St, Pakenham Vic').

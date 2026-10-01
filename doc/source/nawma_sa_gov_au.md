# North Adelaide Waste Management Authority

Support for schedules provided by [North Adelaide Waste Management Authority](https://www.nawma.sa.gov.au).

Source for nawma.sa.gov.au (Salisbury, Playford, and Gawler South Australia).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: nawma_sa_gov_au
      args:
        street_number: STREET_NUMBER
        street_name: STREET_NAME
        suburb: SUBURB
```

### Configuration Variables

**street_number**  
*(string) (optional)*

**street_name**  
*(string) (required)*

**suburb**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: nawma_sa_gov_au
      args:
        street_number: '128'
        street_name: Bridge Road
        suburb: Pooraka
```

## How to get the source arguments

Enter the street, suburb and optionally the house number as they appear on the [NAWMA collection day lookup](https://www.nawma.sa.gov.au/).

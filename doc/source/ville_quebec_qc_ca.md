# Québec (QC)

Support for schedules provided by [Québec (QC)](https://www.ville.quebec.qc.ca/services/info-collecte/).

Source script for Québec city waste collection

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ville_quebec_qc_ca
      args:
        street_number_and_name: STREET_NUMBER_AND_NAME
        unique_id: UNIQUE_ID
```

### Configuration Variables

**street_number_and_name**  
*(string) (required)*

**unique_id**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ville_quebec_qc_ca
      args:
        street_number_and_name: 430 4e rue
        unique_id: 219232-134009
```

## How to get the source arguments

You need to provide your street number and name in Quebec City.

# RMR Lac-Saint-Jean (QC)

Support for schedules provided by [RMR Lac-Saint-Jean (QC)](https://calendrier.rmrlac.qc.ca).

Source script for RMR Lac-Saint-Jean waste collection

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: rmrlac_qc_ca
      args:
        street_number_and_name: STREET_NUMBER_AND_NAME
        locality: LOCALITY
```

### Configuration Variables

**street_number_and_name**  
*(string) (required)*

**locality**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: rmrlac_qc_ca
      args:
        street_number_and_name: 1201 16e Chemin
        locality: "M\xE9tabetchouan-Lac-\xE0-la-Croix"
```

## How to get the source arguments

Enter your street number and name along with your municipality, e.g. '1201 16e Chemin' in 'Métabetchouan-Lac-à-la-Croix'.

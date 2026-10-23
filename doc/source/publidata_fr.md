# Publidata generic source

Support for schedules provided by [Publidata generic source](https://www.publidata.io/fr/).

Publidata is a French public operator with a reach of up to 6M inhabitants. Check if your area is concerned on their website.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: publidata_fr
      args:
        address: ADDRESS
        insee_code: INSEE_CODE
        instance_id: INSTANCE_ID
        public_type: PUBLIC_TYPE
```

### Configuration Variables

**address**  
*(string) (required)*

**insee_code**  
*(string) (required)*

**instance_id**  
*(string) (required)*

**public_type**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: publidata_fr
      args:
        address: 1 rue de Paris
        insee_code: '78481'
        instance_id: 1420
```

## How to get the source arguments

Enter your street address (number and street name only, without city or postcode). Find your commune's current INSEE code at https://www.insee.fr/fr/recherche/recherche-geographique; merged communes (communes nouvelles) have a new code. The `instance_id` is pre-filled when you select a known service provider; for an unlisted one, find it with the browser's network inspector on the provider's waste widget. `public_type` (`individual_housing` or `collective_housing`) is only needed where the schedules differ per housing type.

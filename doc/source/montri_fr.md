# Montri

Support for schedules provided by [Montri](https://montri.fr).

Source for Montri, a French waste collection schedule platform used by several intercommunal waste-management syndicates (e.g. SICOVAD around Épinal).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: montri_fr
      args:
        postal_code: POSTAL_CODE
        city_name: CITY_NAME
        address: ADDRESS
```

### Configuration Variables

**postal_code**  
*(string) (required)*

**city_name**  
*(string) (required)*

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: montri_fr
      args:
        postal_code: '88000'
        city_name: "Dinoz\xE9"
        address: 6 Place Georges Boizot
```

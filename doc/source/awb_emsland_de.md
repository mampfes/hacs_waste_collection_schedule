# Abfallwirtschaftsbetrieb Emsland

Support for schedules provided by [Abfallwirtschaftsbetrieb Emsland](https://www.awb-emsland.de).

Source for AWB Emsland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: awb_emsland_de
      args:
        city: CITY
        street: STREET
        house_number: HOUSE_NUMBER
        address_suffix: ADDRESS_SUFFIX
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (required)*

**house_number**  
*(string) (required)*

**address_suffix**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: awb_emsland_de
      args:
        city: Andervenne
        street: Am Gallenberg
        house_number: '1'
```

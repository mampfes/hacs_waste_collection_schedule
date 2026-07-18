# Rhein-Hunsrück Entsorgung (RHE)

Support for schedules provided by [Rhein-Hunsrück Entsorgung (RHE)](https://www.rh-entsorgung.de).

Source for RHE (Rhein Hunsrück Entsorgung).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: rh_entsorgung_de
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
    - name: rh_entsorgung_de
      args:
        city: "Rheinb\xF6llen"
        street: "Erbacher Stra\xDFe"
        house_number: 13
        address_suffix: A
```

## How to get the source arguments

Pick the 'service_id' for your region from the source's list of municipalities, then enter your town ('city') and where required the street ('street') and house number ('house_number'). Alternatively provide a known 'city_id' and 'area_id' directly.

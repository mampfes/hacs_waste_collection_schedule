# Montpellier Méditerranée Métropole

Support for schedules provided by [Montpellier Méditerranée Métropole](https://data.montpellier3m.fr).

Source for waste collection schedules in Montpellier Méditerranée Métropole, France.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: data_montpellier3m_fr
      args:
        street_name: STREET_NAME
        house_number: HOUSE_NUMBER
        commune: COMMUNE
```

### Configuration Variables

**street_name**  
*(string) (required)*

**house_number**  
*(string) (optional)*

**commune**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: data_montpellier3m_fr
      args:
        street_name: Rue Parlier
        house_number: 3
        commune: MONTPELLIER
```

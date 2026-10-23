# Samverkan Återvinning Miljö (SÅM)

Support for schedules provided by [Samverkan Återvinning Miljö (SÅM)](https://www.samiljo.se).

Source for Samverkan Återvinning Miljö (SÅM) waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: samiljo_se
      args:
        street: STREET
        city: CITY
```

### Configuration Variables

**street**  
*(string) (required)*

**city**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: samiljo_se
      args:
        city: Reftele
        street: Storgatan 6
```

## How to get the source arguments

Enter the street name with number and the city as they appear in the calendar search on https://www.samiljo.se. Collections in a holiday week are marked 'Helgvecka' in the description.

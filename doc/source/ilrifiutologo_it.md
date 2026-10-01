# Il Rifiutologo

Support for schedules provided by [Il Rifiutologo](https://ilrifiutologo.it).

Source for ilrifiutologo.it

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ilrifiutologo_it
      args:
        town: TOWN
        street: STREET
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**town**  
*(string) (required)*

**street**  
*(string) (required)*

**house_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ilrifiutologo_it
      args:
        town: Faenza
        street: VIA AUGUSTO RIGHI
        house_number: '6'
```

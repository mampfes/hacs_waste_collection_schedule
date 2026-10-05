# Renosyd

Support for schedules provided by [Renosyd](https://renosyd.dk).

Renosyd collections for Skanderborg and Odder kommunes

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: renosyd_dk
      args:
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**house_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: renosyd_dk
      args:
        house_number: '013000'
```

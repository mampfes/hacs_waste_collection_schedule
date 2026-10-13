# Reno Djurs

Support for schedules provided by [Reno Djurs](https://renodjurs.dk).

Reno Djurs collections for Djursland

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: renodjurs_dk
      args:
        id: ID
```

### Configuration Variables

**id**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: renodjurs_dk
      args:
        id: '46000'
```

## How to get the source arguments

Open https://minside.renodjurs.dk, search your address and copy the number after `id=` in the address bar of the 'Ordninger' page.

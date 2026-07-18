# Lobbe App

Support for schedules provided by [Lobbe App](https://lobbe.app/).

Source for Lobbe App.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: lobbe_app
      args:
        state: STATE
        city: CITY
        street: STREET
```

### Configuration Variables

**state**  
*(string) (required)*

**city**  
*(string) (required)*

**street**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: lobbe_app
      args:
        state: Hessen
        city: Diemelsee
        street: Am Breuschelt
```

# Republic Services

Support for schedules provided by [Republic Services](https://www.republicservices.com).

Source for Republic Services Collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: republicservices_com
      args:
        street_address: STREET_ADDRESS
        method: METHOD
```

### Configuration Variables

**street_address**  
*(string) (required)*

**method**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: republicservices_com
      args:
        street_address: 101 E Main St, Georgetown, KY 40324
        method: 1
```

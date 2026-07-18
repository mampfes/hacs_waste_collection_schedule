# 1Coast - Central Coast

Support for schedules provided by [1Coast - Central Coast](https://1coast.com.au/).

Source for 1Coast - Central Coast.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: 1coast_com_au
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: 1coast_com_au
      args:
        address: 9 RHODIN DR, LONG JETTY CENTRAL COAST 2261
```

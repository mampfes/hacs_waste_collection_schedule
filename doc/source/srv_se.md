# SRV återvinning AB

Support for schedules provided by [SRV återvinning AB](https://www.srvatervinning.se/), Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: srv_se
      args:
        address: address
```

### Configuration Variables

**address**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: srv_se
      args:
        address: "Skansvägen"

```

## How to get the source arguments

1. Go to your calendar at [SRV återvinning AB](https://www.srvatervinning.se/sophamtning/privat/hamtinformation-och-driftstorningar)
2. Enter your address.
3. Copy the exact values from the textboxes in the source configuration. 

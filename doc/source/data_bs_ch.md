# Basel-Stadt

Support for schedules provided by [Basel-Stadt](https://data.bs.ch).

Source for waste collection schedule of Basel-Stadt, Switzerland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: data_bs_ch
      args:
        zone: ZONE
```

### Configuration Variables

**zone**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: data_bs_ch
      args:
        zone: A
```

## How to get the source arguments

Your waste collection zone (A-H or GUF).

# Lindau

Support for schedules provided by [Lindau](https://www.lindau.ch).

Source for Lindau waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: lindau_ch
      args:
        city: CITY
```

### Configuration Variables

**city**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: lindau_ch
      args:
        city: Tagelswangen
```

## How to get the source arguments

Enter your village as listed on https://www.lindau.ch/abfalldaten (Grafstal, Lindau, Tagelswangen or Winterberg).

# Chesapeake, VA

Support for schedules provided by [Chesapeake, VA](https://www.cityofchesapeake.net).

Source for Chesapeake, VA trash collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: chesapeake_va_us
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
    - name: chesapeake_va_us
      args:
        address: 460 Sawyers Mill Xing, Chesapeake, VA 23323
```

## How to get the source arguments

Enter your full street address including city and state (e.g. '460 Sawyers Mill Xing, Chesapeake, VA 23323').

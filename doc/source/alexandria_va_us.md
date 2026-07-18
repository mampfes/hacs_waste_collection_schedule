# Alexandria, VA

Support for schedules provided by [Alexandria, VA](https://www.alexandriava.gov/RefuseCollection).

Source for City of Alexandria, VA trash, recycling and leaf collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: alexandria_va_us
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
    - name: alexandria_va_us
      args:
        address: 301 King St, Alexandria, VA 22314
```

## How to get the source arguments

Enter your full street address including city and state (e.g. '301 King St, Alexandria, VA 22314').

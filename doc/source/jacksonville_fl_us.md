# Jacksonville, FL

Support for schedules provided by [Jacksonville, FL](https://myjax.custhelp.com/app/hauler).

Source for Jacksonville, FL waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: jacksonville_fl_us
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
    - name: jacksonville_fl_us
      args:
        address: 1 EverBank Stadium Dr, Jacksonville, FL
```

## How to get the source arguments

Use the same address you would enter on the MyJax hauler lookup page.

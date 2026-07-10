# Jacksonville, FL

Support for schedules provided by [MyJax Hauler Lookup](https://myjax.custhelp.com/app/hauler).

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

Full street address including city and state.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: jacksonville_fl_us
      args:
        address: 11743 Heather Grove Ln, Jacksonville, FL
```

## How to get the source arguments

Use the same street address you would enter on the MyJax hauler lookup page. The source geocodes the address and returns the next dated pickups supplied by Jacksonville's hauler lookup service.

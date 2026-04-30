# Baton Rouge, LA

Support for schedules provided by [Baton Rouge, LA](https://www.brla.gov/337/Garbage-Collection).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: batonrouge_la_us
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
    - name: batonrouge_la_us
      args:
        address: 222 Saint Louis St, Baton Rouge, LA 70802
```

## How to get the source arguments

Visit the Baton Rouge [My Government Services](https://experience.arcgis.com/experience/a20b47125fa2406691b37860fc004fa1/page/My-Government-Services/) portal and search for your address. Use your full street address including city and state (e.g. "222 Saint Louis St, Baton Rouge, LA 70802").

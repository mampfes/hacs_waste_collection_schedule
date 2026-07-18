# Baton Rouge, LA

Support for schedules provided by [Baton Rouge, LA](https://www.brla.gov/337/Garbage-Collection).

Source for Baton Rouge, LA waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: baton_rouge_la_us
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
    - name: baton_rouge_la_us
      args:
        address: 222 Saint Louis St, Baton Rouge, LA 70802
```

## How to get the source arguments

Enter your street address within Baton Rouge, LA (e.g. '222 Saint Louis St, Baton Rouge, LA 70802').

# Telge Återvinning

Support for schedules provided by [Telge Återvinning](https://www.telge.se).

Source for Telge Återvinning, household waste collection in Södertälje municipality

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: telge_se
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
    - name: telge_se
      args:
        address: "BERGSGATAN 22, S\xD6DERT\xC4LJE"
```

## How to get the source arguments

Find your address at https://www.telge.se by searching for your street name in the waste collection schedule (Sopbilsschema). Use the exact address string shown in the autocomplete dropdown, e.g. 'BERGSGATAN 22, SÖDERTÄLJE'.

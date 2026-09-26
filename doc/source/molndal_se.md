# Mölndal

Support for schedules provided by [Mölndal](https://molndal.se).

Source for Mölndal waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: molndal_se
      args:
        facility_id: FACILITY_ID
```

### Configuration Variables

**facility_id**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: molndal_se
      args:
        facility_id: '105000'
```

## How to get the source arguments

Search your address at https://future.molndal.se/FutureWeb/SimpleWastePickup and use the number in brackets as 'facility_id'.

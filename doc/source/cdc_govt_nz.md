# Carterton District Council

Support for schedules provided by [Carterton District Council](https://cdc.govt.nz).

Source for Carterton District Council (NZ) urban rubbish and recycling collections.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cdc_govt_nz
      args:
        sticker: STICKER
        collection_day: COLLECTION_DAY
```

### Configuration Variables

**sticker**  
*(string) (required)*

**collection_day**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: cdc_govt_nz
      args:
        sticker: '1'
        collection_day: Monday
```

## How to get the source arguments

The sticker on your recycling wheelie bin shows a 1 or a 2 and your collection day. Choose both. Week 1 and week 2 are the red and blue weeks of the calendar on https://cdc.govt.nz/services/sustainability/recycling/.

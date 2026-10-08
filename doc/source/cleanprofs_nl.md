# CleanProfs

Support for schedules provided by [CleanProfs](https://www.cleanprofs.nl).

Container cleaning schedules provided by CleanProfs.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cleanprofs_nl
      args:
        postcode: POSTCODE
        house_number: HOUSE_NUMBER
        suffix: SUFFIX
```

### Configuration Variables

**postcode**  
*(string) (required)*

**house_number**  
*(string) (required)*

**suffix**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: cleanprofs_nl
      args:
        postcode: 2291PG
        house_number: '12'
```

## How to get the source arguments

Enter the postcode, house number and optional house-number addition of an address registered with CleanProfs.

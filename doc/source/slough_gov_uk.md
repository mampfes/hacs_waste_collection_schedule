# Slough Borough Council

Support for schedules provided by [Slough Borough Council](https://www.slough.gov.uk).

Source for slough.gov.uk services for Slough Borough Council.

## Configuration via configuration.yaml

### Using record_id

```yaml
waste_collection_schedule:
  sources:
    - name: slough_gov_uk
      args:
        record_id: RECORD_ID
```

### Using street

```yaml
waste_collection_schedule:
  sources:
    - name: slough_gov_uk
      args:
        street: STREET
```

### Configuration Variables

**record_id**  
*(string) (alternative)*

**street**  
*(string) (alternative)*

Provide one of: `record_id` or `street`.

## Example

### Using record_id

```yaml
waste_collection_schedule:
  sources:
    - name: slough_gov_uk
      args:
        record_id: 34771
```

### Using street

```yaml
waste_collection_schedule:
  sources:
    - name: slough_gov_uk
      args:
        street: Knolton Way, Montgomery Place
```

## How to get the source arguments

Search for your street at https://www.slough.gov.uk/bin-collections and note the number from the URL of your matching result (for example 34771 from /directory-record/34771/...). Use that number as the directory record ID, or give the exact street name as listed in the directory instead (for example 'Knolton Way, Montgomery Place'). Use one of the two, not both.

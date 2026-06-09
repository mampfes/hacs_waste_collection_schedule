# Slough Borough Council

Support for schedules provided by [Slough Borough Council](https://www.slough.gov.uk), serving Slough, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: slough_gov_uk
      args:
        record_id: RECORD_ID
```

### Configuration Variables

**record_id**
*(Integer) (optional)*

The numeric ID from the Slough bin directory URL (e.g. `34771` from `/directory-record/34771/...`). Use this **or** `street`, not both.

**street**
*(String) (optional)*

The name of your street as listed in the Slough bin directory (e.g. `Knolton Way, Montgomery Place`). Use this **or** `record_id`, not both.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: slough_gov_uk
      args:
        record_id: 34771
```

## How to find your `record_id`

1. Go to [https://www.slough.gov.uk/bin-collections](https://www.slough.gov.uk/bin-collections)
2. Enter your street name in the search box
3. Click the matching result — the URL will look like `/directory-record/34771/knolton-way-montgomery-place`
4. The number (e.g. `34771`) is your `record_id`

Alternatively, pass your street name exactly as shown in the search results using the `street` argument.

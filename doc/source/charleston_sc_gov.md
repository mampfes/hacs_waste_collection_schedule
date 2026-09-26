# Charleston, SC

Support for schedules provided by [Charleston, SC](https://www.charleston-sc.gov/345/Environmental-Services).

Source for City of Charleston, SC garbage and trash/yard-waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: charleston_sc_gov
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
    - name: charleston_sc_gov
      args:
        address: 123 Coming St, Charleston, SC 29403
```

## How to get the source arguments

Enter the full street address including city, state, and ZIP code.

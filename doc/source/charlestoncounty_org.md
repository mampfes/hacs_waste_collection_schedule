# Charleston County, SC

Support for schedules provided by [Charleston County, SC](https://www.charlestoncounty.org/departments/environmental-management/recycle.php).

Source for Charleston County, SC residential curbside recycling.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: charlestoncounty_org
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
    - name: charlestoncounty_org
      args:
        address: 123 Coming St, Charleston, SC 29403
```

## How to get the source arguments

Enter the full street address including city, state, and ZIP code.

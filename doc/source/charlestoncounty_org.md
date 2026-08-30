# Charleston County, SC

Support for residential curbside recycling schedules published by [Charleston County Environmental Management](https://www.charlestoncounty.org/departments/environmental-management/recycle.php).

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

Full street address including city, state, and ZIP code.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: charlestoncounty_org
      args:
        address: "123 Coming St, Charleston, SC 29403"
```

The source uses Charleston County's live curbside recycling route map. It is intended for eligible single-family residences; businesses, schools, apartments, and condominiums use separate county schedules.

The county publishes the next exact collection date for each biweekly route. The source uses that official date as an anchor and projects the following biweekly occurrences forward, rather than predicting holiday adjustments to the published date itself.

# Derby City Council

Support for schedules provided by [Derby City Council](https://secure.derby.gov.uk/binday/), serving the
city of Derby, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: derby_gov_uk
      args:
        premises_id: PREMISES_ID
```

### Configuration Variables

**premises_id**  
*(int) (required if post_code not provided)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: derby_gov_uk
      args:
        premises_id: 100030339868
```

## How to get the premises_id argument

The premises_id can be found in the URL when looking up your
bin collection days at [Derby City Councils bin day page](https://secure.derby.gov.uk/binday/).

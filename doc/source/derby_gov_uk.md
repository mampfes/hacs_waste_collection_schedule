# Derby City Council

Support for schedules provided by [Derby City Council](https://secure.derby.gov.uk/binday/), serving the
city of Derby, UK.

## Configuration via configuration.yaml

(recommended)
```yaml
waste_collection_schedule:
    sources:
    - name: derby_gov_uk
      args:
        premises_id: PREMISES_ID
```

or (not recommended)

```yaml
waste_collection_schedule:
    sources:
        - name: derby_gov_uk
          args:
            post_code: DE1 1ED
            house_number: 1
```

### Configuration Variables

**premises_id**<br>
*(int) (required if post_code not provided)*

**post_code**<br>
*(string) (required if premises_id not provided)*

**house_number**<br>
*(int) (required if premises_id not provided)*

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

## Why premises_id over post_code and house number?

The code has to do a search by post code and house number then look up the bin collection time using premises ID.

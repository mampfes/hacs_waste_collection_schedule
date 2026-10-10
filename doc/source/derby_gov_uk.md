# Derby City Council

Support for schedules provided by [Derby City Council](https://derby.gov.uk).

Source for Derby.gov.uk services for Derby City Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: derby_gov_uk
      args:
        premises_id: PREMISES_ID
        post_code: POST_CODE
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**premises_id**  
*(string) (required)*

**post_code**  
*(string) (optional)*

**house_number**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: derby_gov_uk
      args:
        premises_id: '10010688168'
```

## How to get the source arguments

Search your address on <https://secure.derby.gov.uk/binday>. The url will contain your premises ID, e.g. `https://secure.derby.gov.uk/binday/BinDays/10010688168?...` where `10010688168` is the premises ID. Leave post_code and house_number empty: they are no longer used.

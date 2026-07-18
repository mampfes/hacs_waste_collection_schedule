# Peterborough City Council

Support for schedules provided by [Peterborough City Council](https://peterborough.gov.uk).

Source for peterborough.gov.uk services for Peterborough.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: peterborough_gov_uk
      args:
        post_code: POST_CODE
        uprn: UPRN
```

### Configuration Variables

**post_code**  
*(string) (required)*

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: peterborough_gov_uk
      args:
        post_code: PE57AX
        uprn: '100090214774'
```

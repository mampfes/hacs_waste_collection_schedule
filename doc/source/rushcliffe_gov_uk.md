# Rushcliffe Brough Council

Support for schedules provided by [Rushcliffe Brough Council](https://www.rushcliffe.gov.uk/).

Source for Rushcliffe Brough Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: rushcliffe_gov_uk
      args:
        postcode: POSTCODE
        address: ADDRESS
```

### Configuration Variables

**postcode**  
*(string) (required)*

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: rushcliffe_gov_uk
      args:
        postcode: NG12 5FE
        address: 2 Church Drive, Keyworth, NOTTINGHAM, NG12 5FE
```

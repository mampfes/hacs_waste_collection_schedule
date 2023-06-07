# Tonbridge & Malling Borough Council

Support for schedules provided by [Tonbridge and Malling Borough Council](https://www.tmbc.gov.uk/xfp/form/167), serving Tonbridge and Malling, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: tmbc_gov_uk
      args:
        post_code: Post Code
        address: Address
```

### Configuration Variables

**post_code**  
*(string) (required)*

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: tmbc_gov_uk
      args:
        post_code: "ME19 6NE"
        address: "138 High Street"
```

## How to verify that your address works

Visit [tmbc.gov.uk](https://www.tmbc.gov.uk/xfp/form/167) page and search for your address. The string you select as Address (only starts with is checked, so you can stop after the street) should match exactly your address parameter.

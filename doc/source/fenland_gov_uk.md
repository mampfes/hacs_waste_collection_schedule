# Fenland District Council

Support for schedules provided by [Fenland District Council](https://www.fenland.gov.uk/find), serving Fenland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: fenland_gov_uk
      args:
        post_code: POST_CODE
        house_number: NUMBER
```

### Configuration Variables

**POST_CODE**
*(string) (required)*

**HOUSE_NUMBER**
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: fenland_gov_uk
      args:
        post_code: "PE15 0SD"
        house_number: "1"
```
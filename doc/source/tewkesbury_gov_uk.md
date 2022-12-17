# Tewkesbury City Council

Support for upcoming schedules provided by [Tewkesbury City Council](https://www.tewkesbury.gov.uk/waste-and-recycling), serving Tewkesbury (UK) and areas of Gloucestershire.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: tewkesbury_gov_uk
      args:
        postcode: POSTCODE
```

### Configuration Variables

**POST_CODE**<br>
*(string) (required)*


## Example

```yaml
waste_collection_schedule:
    sources:
    - name: tewkesbury_gov_uk
      args:
        postcode: "GL20 5TT"
```

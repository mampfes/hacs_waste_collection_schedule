# Cheshire West and Chester Council

Support for schedules provided by [Cheshire West and Chester Council](https://www.cheshirewestandchester.gov.uk).

Source for waste collection services for Cheshire West and Chester Council

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cheshire_west_and_chester_gov_uk
      args:
        uprn: UPRN
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: cheshire_west_and_chester_gov_uk
      args:
        uprn: 100010030086
```

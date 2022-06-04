# Wakefield Council

Support for schedules provided by [Wakefield Council](https://www.wakefield.gov.uk/site/Where-I-Live-Results), serving the borough of Wakefield, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: wakefieldt_gov_uk
      args:
        uprn: UPRN
```


### Configuration Variables

**uprn**<br>
*(string) (required)*



## Examples

```yaml
waste_collection_schedule:
    sources:
    - name: wakefield_gov_uk
      args:
        uprn: 63161064
```

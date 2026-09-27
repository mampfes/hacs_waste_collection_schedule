# South Staffordshire Council

Support for schedules provided by [South Staffordshire Council](https://sstaffs.gov.uk/).

Source for waste collection services for South Staffordshire Council

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sstaffs_gov_uk
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
    - name: sstaffs_gov_uk
      args:
        uprn: '100031831923'
```

# Environment First

Support for schedules provided by [Environment First](https://environmentfirst.co.uk).

Consolidated source for waste collection services from:
        Eastbourne Borough Council
        Lewes District Council
        

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: environmentfirst_co_uk
      args:
        post_code: POST_CODE
        number: NUMBER
        name: NAME
        uprn: UPRN
```

### Configuration Variables

**post_code**  
*(string) (optional)*

**number**  
*(string) (optional)*

**name**  
*(string) (optional)*

**uprn**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: environmentfirst_co_uk
      args:
        uprn: '100060063421'
```

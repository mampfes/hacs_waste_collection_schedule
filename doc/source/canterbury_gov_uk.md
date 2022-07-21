# Canterbury City Council

Support for schedules provided by [Canterbury City Council](https://www.canterbury.gov.uk/bins-and-waste/find-your-bin-collection-dates/), serving Canterbury (UK) and parts of Kent.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: canterbury_gov_uk
      args:
        post_code: POST_CODE
        number: NUMBER

```

### Configuration Variables

**POST_CODE**<br>
*(string) (required)*

**NUMBER**<br>
*(string) (required)*


## Examples

```yaml
waste_collection_schedule:
    sources:
    - name: canterbury_gov_uk
      args:
        post_code: "ct68ru"
        number: "63"
```
 
```yaml
waste_collection_schedule:
    sources:
    - name: canterbury_gov_uk
      args:
        post_code: "ct68ru"
        number: "KOWLOON"
```

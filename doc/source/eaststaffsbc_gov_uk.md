# East Staffordshire Borough Council

Support for schedules provided by [East Staffordshire Borough Council](https://www.eaststaffsbc.gov.uk/bins-rubbish-recycling/collection-dates), UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: eaststaffsbc_gov_uk
      args:
        uid: UID
```

### Configuration Variables

**uid**</br>
*(integer | string) (required)*
The unique identifier East Staffs has assigned your property.


## Example
```yaml
waste_collection_schedule:
    sources:
    - name: eaststaffsbc_gov_uk
      args:
        uid: 103368
```

#### How to find your `UID`
Go to the [East Staffordshire Borough Council](https://www.eaststaffsbc.gov.uk/bins-rubbish-recycling/collection-dates) website and search for your collection schedule. Your UID is the number at the end of the url when the page showing your collection dates is displayed. For example: <br>
_www.eaststaffsbc.gov.uk/bins-rubbish-recycling/collection-dates/`103366`_




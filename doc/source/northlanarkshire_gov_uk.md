# North Lanarkshire Council

Support for schedules provided by [North Lanarkshire Council](https://northlanarkshire.gov.uk).

Source for waste collection services for North Lanarkshire Council

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: northlanarkshire_gov_uk
      args:
        uprn: UPRN
        usrn: USRN
```

### Configuration Variables

**uprn**  
*(string) (required)*

**usrn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: northlanarkshire_gov_uk
      args:
        uprn: '118026605'
        usrn: '48406574'
```

## How to get the source arguments

Look your address up on the council's bin collection dates page; its URL has the form www.northlanarkshire.gov.uk/bin-collection-dates/UPRN/USRN.

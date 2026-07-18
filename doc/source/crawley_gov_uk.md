# Crawley Borough Council (myCrawley)

Support for schedules provided by [Crawley Borough Council (myCrawley)](https://crawley.gov.uk/).

Source for Crawley Borough Council (myCrawley).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: crawley_gov_uk
      args:
        uprn: UPRN
        usrn: USRN
```

### Configuration Variables

**uprn**  
*(string) (required)*

**usrn**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: crawley_gov_uk
      args:
        uprn: '100061775179'
```

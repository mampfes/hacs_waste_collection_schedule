# Crawley Borough Council (myCrawley)

Support for schedules provided by [Crawley Borough Council (myCrawley)](https://crawley.gov.uk/), serving Crawley Borough, GB.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: crawley_gov_uk
      args:
        uprn: UPRN
        
```

### Configuration Variables

**uprn**  
*(String | Integer) (required)*

**usrn**  
*(String | Integer) (optional), Probably not needed*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: crawley_gov_uk
      args:
        uprn: 100061775179   
```

```yaml
waste_collection_schedule:
    sources:
    - name: crawley_gov_uk
      args:
        uprn: 100061787552
        usrn: 9700731
        
```

## How to get the source argument

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.

USRN map: <https://uprn.uk/usrn-map>

# East Northamptonshire and Wellingborough

Support for schedules provided by [East Northamptonshire](east-northamptonshire.gov.uk) and [Wellingborough](wellingborough.gov.uk), serving East Northamptonshire and Wellingborough, GB.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: east_northamptonshire_gov_uk
      args:
        uprn: UPRN       
```

### Configuration Variables

**uprn**  
*(string | Integer) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: east_northamptonshire_gov_uk
      args:
        uprn: 100031040850        
```

## How to get the source argument

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.

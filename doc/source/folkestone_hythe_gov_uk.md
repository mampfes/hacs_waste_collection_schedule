# Folkestone & Hythe District Council, United Kingdom

Support for schedules provided by [Folkestone & Hythe District Council, United Kingdom](https://www.folkestone-hythe.gov.uk/recycling-waste-bins).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: folkestone_hythe_gov_uk
      args:
        uprn: "UPRN"
        
```

### Configuration Variables

**uprn**  
*(String | Integer) (required)*


## Example

```yaml
waste_collection_schedule:
    sources:
    - name: folkestone_hythe_gov_uk
      args:
        uprn: "50032102"
        
```

## How to get the source argument

Your UPRN is displayed on the council web site underneath your address when it displays your bin collection schedule.
An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.

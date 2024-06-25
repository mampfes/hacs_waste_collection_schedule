# Darlington Borough Council

Support for schedules provided by [Darlington Borough Council](https://darlington.gov.uk), serving Darlington, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: darlington_gov_uk
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
    - name: darlington_gov_uk
      args:
        uprn: "010013315817"
```

```yaml
waste_collection_schedule:
    sources:
    - name: darlington_gov_uk
      args:
        uprn: 100110560916
```

## How to get the source argument

You can find your UPRN in your address bar after searching your address (<https://www.darlington.gov.uk/bins-waste-and-recycling/weekly-refuse-and-recycling-collection-lookup/>) and clicking one of the 'Print `CALENDER_TYPE` calendar' button.

Another easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.

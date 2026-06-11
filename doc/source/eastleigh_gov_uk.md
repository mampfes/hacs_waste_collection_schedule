# Eastleigh Borough Council

Support for schedules provided by [Eastleigh Borough Council](https://eastleigh.gov.uk), serving Eastleigh Borough, Hampshire, UK.

## Local Government Reorganisation note
During the ongoing local government reorganisation (LGR) in Hampshire, please continue to use the source for your current area as long as it's still working. New sources for the new South West Hampshire Council are not expected to be live until at least April 2028, when the council itself officially comes into being.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: eastleigh_gov_uk
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
    - name: eastleigh_gov_uk
      args:
        uprn: "100060319000"
        
```

## How to get the source argument

You can see your uprn in your url bar when after selecting your address at <https://eastleigh.gov.uk/waste-bins-and-recycling/collection-dates>

An other way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.

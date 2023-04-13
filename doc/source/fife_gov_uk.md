# Fife Council

Support for schedules provided by [Fife Council](https://www.fife.gov.uk), serving Fife Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: fife_gov_uk
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
    - name: fife_gov_uk
      args:
        uprn: "320069189"
        
```

### How to find your `UPRN`

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
Otherwise you can inspect the web requests the Fife Council website makes when entering in your postcode and then selecting your address.

### A more complete example with type names shown

Here's a more complete example of the sources to demonstrate the type names that come back from Fife's API (at time of writing):

```yaml
waste_collection_schedule:
  sources:
    - name: fife_gov_uk
      args:
        uprn: "320069189"
      customize:
        - type: "Food and Garden Waste / Brown Bin"
          alias: "Brown Bin"
        - type: "Landfill / Blue Bin"
          alias: "Blue Bin"
        - type: "Paper and Cardboard / Grey Bin"
          alias: "Grey Bin"
        - type: "Cans and Plastics / Green Bin"
          alias: "Green Bin"
  day_switch_time: "18:00"
  
```


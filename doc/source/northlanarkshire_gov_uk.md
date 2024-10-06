# North Lanarkshire Council, United Kingdom

Support for schedules provided by [North Lanarkshire Council](https://www.northlanarkshire.gov.uk/bin-collection-dates), serving North Lanarkshire, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: northlanarkshire_gov_uk
      args:
        uprn: "UPRN"
        usrn: "USRN"
        
```

### Configuration Variables

**uprn**  
*(String | Integer) (required)*

**usrn**  
*(String | Integer) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: northlanarkshire_gov_uk
      args:
        uprn: "118026605"
        usrn: "48406574"
        
```

## How to get the source arguments

The easiest way to get the source arguements is to look at the url of the web page that displays your collection schedule. The url has the format:
`www.northlanarkshire.gov.uk/bin-collection-dates/UPRN/USRN`

Alternatively, an easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.

Your Unique Street Reference Number (USRN) can be found by searching for your address at  <https://uprn.uk/> and viewing the _Data Associations_ section.


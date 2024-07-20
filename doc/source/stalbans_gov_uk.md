# St Albans City & District Council

Support for schedules provided by [St Albans City & District Council](https://stalbans.gov.uk), serving St Albans, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: stalbans_gov_uk
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
    - name: stalbans_gov_uk
      args:
        uprn: "100081132201"
        
```

## How to get the source argument

### Easy way (external website)

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.

### Hard way (browser developer tools)

Goto <https://gis.stalbans.gov.uk/NoticeBoard9/NoticeBoard.aspx>, open your browser developer tools, goto the network tab and inspect the network requests as you select your address. You will see a POST request to `https://gis.stalbans.gov.uk/NoticeBoard9/VeoliaProxy.NoticeBoard.asmx/GetServicesByUprnAndNoticeBoard` you can find the UPRN in the request payload.

# Manchester City Council

Support for schedules provided by [Mansfield District
Council](https://www.mansfield.gov.uk/xfp/form/1327), serving the Mansfield District, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: mansfield_gov_uk
      args:
        uprn: UPRN_CODE
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: mansfield_gov_uk
      args:
        uprn: "200000666900"
```

## How to get the source argument

The UPRN code can be found in the page by entering your postcode on the
[Mansfield District Council Bin Collections](https://www.mansfield.gov.uk/xfp/form/1327) page.  When your collection schedule is showm, your uprn is shown in the url. For example:

portal.mansfield.gov.uk/MDCWhiteSpaceWebService/WhiteSpaceWS.asmx/GetCollectionByUPRNAndDate?apiKey=mDc-wN3-B0f-f4P&UPRN=`100031399487`&coldate=08/09/2023

Alternatively, you can An easy way to find your Unique Property Reference Number (UPRN)  by going to <https://www.findmyaddress.co.uk/> and entering your address details.
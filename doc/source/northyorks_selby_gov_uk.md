# North Yorkshire Council - Selby

Support for schedules provided by [North Yorkshire Council - Selby](https://northyorks.gov.uk), serving North Yorkshire Council - Selby, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: northyorks_selby_gov_uk
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
    - name: northyorks_selby_gov_uk
      args:
        uprn: "100052176620"
        
```

## How to get the source argument

You can find your Unique Property Reference Number (UPRN) by visiting the [North Yorkshire Council - Selby](https://www.northyorks.gov.uk/bin-calendar/lookup) website and entering your address details. You should now see your collection dates. You UPRN will be in the URL of the page. For example, if the URL is `https://www.northyorks.gov.uk/bin-calendar/Selby/results/10013454353`, then your UPRN is `10013454353`.

An other way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.

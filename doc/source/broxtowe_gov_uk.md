# Broxtowe Borough Council

Support for schedules provided by [Broxtowe Borough Council](https://www.broxtowe.gov.uk/), serving Broxtowe Borough Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: broxtowe_gov_uk
      args:
        uprn: UPRN
        postcode: POSTCODE
        
```

### Configuration Variables

**uprn**  
*(String | Integer) (required)*

**postcode**  
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: broxtowe_gov_uk
      args:
        uprn: 100031343805
        postcode: NG9 2NL
        
```

## How to get the source argument

Use your postcode as postcode argument

### Get your UPRN using findmyaddress.co.uk

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering your address details.

### Get Your UPRN analysing browser traffic

- Fill out your postcode at https://selfservice.broxtowe.gov.uk/renderform.aspx?t=217&k=9D2EF214E144EE796430597FB475C3892C43C528 and press `Search`.
- Open your browser developer tools (in most browser `F12` or `right click -> inspect`) and open the `network` tab.
- Select your address.
- Your network tab should recieve a new request, open it.
- Select `request`. You should now see the argument `ctl00$ContentPlaceHolder1$FF5683DDL` containting your UPRN with a U as prefix (example: `ctl00$ContentPlaceHolder1$FF5683DDL: U100031343805` means your UPRN is `100031343805`).

# Greater Cambridge Waste

Support for schedules provided by [Greater Cambridge Waste](https://www.greayercambridgewaste.org), the shared recycling and waste service for Cambridge City Council and South Cambridgeshire District Council, UK

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: greater_cambridge_waste_org
      args:
        uprn: UPRN
        postcode: POSTCODE
        name_or_number: NAME_OR_NUMBER
```

### Configuration Variables

**POST_CODE**  
*(string) (optional)*

**NAME_OR_NUMBER**  
*(integer | string) (optional)*

**UPRN**  
*(integrer | string) (optional)*

You must provide either the UPRN, or the POSTCODE and NAME_OR_NUMBER

## UPRN Example (Preferred)

```yaml
waste_collection_schedule:
    sources:
    - name: greater_cambridge_waste_org
      args:
        uprn: 200004170895
```

## Address Example

```yaml
waste_collection_schedule:
    sources:
    - name: greater_cambridge_waste_org
      args:
        postcode: "CB22 5HT"
        name_or_number: "Rectory Farm Cottage"
```

## How to find your UPRN
An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.

Alternatively, look at the url of the web page displaying your collection schedule. Your UPRN is the number at the end of the url.

For example: _greatercambridgewaste.org/find-your-bin-collection-day#id=`10091624540`_
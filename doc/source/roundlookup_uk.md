# Malvern Hills District Council

Support for schedules provided by multiple UK councils via the roundlookup service.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: roundlookup_uk
      args:
        council: "DISTRRICT" # see below
        uprn: "UPRN"
```

### Configuration Variables

**uprn**  
*(String | Integer) (required)*

**council**  
*(String) (required)*

should be one of the following:

- "Malvern Hills": <https://swict.malvernhills.gov.uk/mhdcroundlookup/HandleSearchScreen>
- "Wychavon": <https://selfservice.wychavon.gov.uk/wdcroundlookup/HandleSearchScreen>
- "Worcester City": <https://selfserve.worcester.gov.uk/wccroundlookup/HandleSearchScreen>

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: roundlookup_uk
      args:
        uprn: "100120597618"
```

## How to get the source argument

### Easy way (with external tool)

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.

### Harder way (with browser developer tools)

1. Go to the Bin day form of your council (see above)
1. Enter your postcode and click "Find address".
1. Right click -> inspect element on the address dropdown.
1. Your UPRN will be in the value attribute of the option tag containing your address.



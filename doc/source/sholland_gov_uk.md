# South Holland District Council

Support for schedules provided by [South Holland District Council](https://www.sholland.gov.uk/), serving South Holland District Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: sholland_gov_uk
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
    - name: sholland_gov_uk
      args:
        uprn: "10002546801"
        postcode: PE11 2FR
        
```

## How to get the source argument

Use your postcode as postcode argument

### How to get your UPRN

#### with findmyaddress.co.uk

An easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.

#### with browsers network analysis tab

- Got to <https://www.sholland.gov.uk/mycollections> and fill in postcode and select an address.
- Open your browsers' developer tools (`right click -> inspect` / `F12`) and switch to the network tab.
- Click Next. Select the first of the newly appeared requests (you might need to scroll up) and select the request tab of this request.
- The second argument of `SHDCWASTECOLLECTIONS_PAGE1_ADDRESSLIST` should contain your UPRN

# Maldon District Council

Support for schedules provided by [Maldon District Council](https://maldon.suez.co.uk/maldon/AddressLookup/LookupAddresses), serving the
district of Maldon, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: maldon_gov_uk
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
    - name: maldon_gov_uk
      args:
        uprn: "200000917928"
```

## How to get the uprn argument above

The UPRN code can be found by entering your postcode or address on the
[Maldon District Council address lookup page
](https://maldon.suez.co.uk/maldon/AddressLookup/LookupAddresses). Enter your postcode and click 'lookup address', then select your address from the drop down list and click 'Next'. Look at the web address (in your browsers address bar) of the page you are now on and it will look like https://maldon.suez.co.uk/maldon/ServiceSummary?uprn=YOURUPRNHERE, the numbers after 'uprn=' are your addresses's UPRN use this in your config.

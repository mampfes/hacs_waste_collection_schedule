# Manchester City Council

Support for schedules provided by [Manchester City
Council](https://www.manchester.gov.uk/bincollections/), serving the
city of Manchester, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: manchester_uk
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
    - name: manchester_uk
      args:
        uprn: "100031540175"
```

## How to get the source argument

### Easy way, using an external tool

- An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
- Or use the https://uprn.uk/ website to find your UPRN with your postcode on a map

### Manual way using the browser's developer tools

- Got <https://www.manchester.gov.uk/bincollections/> and enter your postcode.
- Open your browser's developer tools (F12 / right-click -> Inspect).
- - either open the network tab and select your address from the list and search the new POST request shown in the Network tab for the `uprn` value in the request payload section
  - or inspect the select element containing the addresses, the `value` attribute option tag containing your address is your `UPRN`

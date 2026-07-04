# Westminster City Council

Support for waste collection schedules provided by [Westminster City Council](https://www.westminster.gov.uk), for the City of Westminster in London, UK.

Westminster publishes a recurring **weekly** schedule per street, keyed by USRN (Unique Street Reference Number). This source reads the rubbish and recycling tables for your street and projects the weekly schedule one year ahead. (The street-cleaning schedule is not included.)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: westminster_gov_uk
      args:
        usrn: USRN
```

### Configuration Variables

**usrn** _(string) (required)_: The Unique Street Reference Number (USRN) for your street.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: westminster_gov_uk
      args:
        usrn: "8400172"
```

## How to find your USRN

Your USRN identifies your street. You can find it by:

- Searching your street name at [FindMyAddress](https://www.findmyaddress.co.uk) and reading the USRN, or
- Opening Westminster's own [street-report search](https://transact.westminster.gov.uk/env/streetreport.aspx) for your street and copying the `USRN` value from the page URL.

Examples of valid USRNs:
- `8400172` (Shirland Mews)
- `8400243` (Shirland Road)

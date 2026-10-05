# Westminster City Council

Support for schedules provided by [Westminster City Council](https://www.westminster.gov.uk).

Source for Westminster City Council (London, UK) bin collections.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: westminster_gov_uk
      args:
        usrn: USRN
```

### Configuration Variables

**usrn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: westminster_gov_uk
      args:
        usrn: '8400172'
```

## How to get the source arguments

You need the USRN (Unique Street Reference Number) for your street. Find it by searching your street on https://www.findmyaddress.co.uk or by inspecting the USRN value in the URL of Westminster's own street-report search at https://transact.westminster.gov.uk/env/streetreport.aspx

# City of Doncaster Council

Support for schedules provided by [City of Doncaster Council](https://doncaster.gov.uk).

Source for doncaster.gov.uk services for the City of Doncaster Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: doncaster_gov_uk
      args:
        postcode: POSTCODE
        address: ADDRESS
```

### Configuration Variables

**postcode**  
*(string) (required)*

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: doncaster_gov_uk
      args:
        postcode: DN6 0LF
        address: Askern Methodist Church
```

## How to get the source arguments

Open https://doncaster-wasterecycling.oncreate.app/w/webpage/bin-query and enter your postcode and your house number or name. Use the same postcode and the house number or name of your property as the arguments. If several properties match, the error message lists the exact addresses to choose from.

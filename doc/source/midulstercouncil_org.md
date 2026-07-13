# Mid Ulster District Council

Support for schedules provided by [Mid Ulster District Council](https://www.midulstercouncil.org), serving Mid Ulster District Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: midulstercouncil_org
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
    - name: midulstercouncil_org
      args:
        uprn: "185653615"

```

## How to get the source argument

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details. Alternatively, you can use the address search at <https://collections-midulster.azurewebsites.net/calendar.aspx> and inspect the "Show" button for your address, which contains the UPRN.

# Glasgow City Council

Support for schedules provided by [Glasgow City Council](https://onlineservices.glasgow.gov.uk/forms/RefuseAndRecyclingWebApplication/AddressSearch.aspx), serving the
city of Glasgow, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: glasgow_gov_uk
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
    - name: glasgow_gov_uk
      args:
        uprn: "906700099060"
```

## How to get the uprn argument above

The UPRN code can be found by entering your postcode or address on the
[Glasgow City Council Bin Collections page
](https://onlineservices.glasgow.gov.uk/forms/RefuseAndRecyclingWebApplication/AddressSearch.aspx).  When on the address list click the 'select' link for your address then on the calendar page look in the browser address bar for your UPRN code e.g. https://onlineservices.glasgow.gov.uk/forms/RefuseAndRecyclingWebApplication/CollectionsCalendar.aspx?UPRN=YOURUPRNSHOWNHERE.

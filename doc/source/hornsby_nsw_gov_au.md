# Hornsby Shire Council

Support for schedules published via PDF by [Hornsby Shire Council](https://hscenquiry.hornsby.nsw.gov.au/Pages/XC.Track/SearchPropertyWaste.aspx).
Note that because information is embebdded in PDFs, but uses a pattern, the actual source connects and pulls data from a third party API.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hornsby_nsw_gov_au
      args:
        property_id: 123456
```

### Configuration Variables

**property_id**
*(int) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: hornsby_nsw_gov_au
      args:
        property_id: 123456
```

## How to get the source arguments
Visit the Hornsby Shire Council bulk waste property search: https://hscenquiry.hornsby.nsw.gov.au/Pages/XC.Track/SearchPropertyWaste.aspx. Search for your address, and a new page will appear. The required `property_id` value can be found both on the end of the URL (SearchPropertyWaste.aspx?id=123456) or listed on the page under Property Number.

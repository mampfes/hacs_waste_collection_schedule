# Impact Apps

Support for schedules provided by [impactapps.com.au](https://impactapps.com.au/). ImpactApps are the creators of the platform used by several councils in Australia to provide waste collection schedules. The API is hosted as a subdomain of `waste-info.com.au` for each council.

Some of the supported councils are available at [calendars.impactapps.com.au](https://calendars.impactapps.com.au/), however, not all councils are listed there.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: impactapps_com_au
      args:
        service: COUNCIL_NAME or API URL
        property_id: PROPERTY_ID
        suburb: SUBURB
        street_name: STREET_NAME
        street_number: STREET_NUMBER
```

### Configuration Variables

**service**
*(string) (required)*

The service can be provided in 1 of 3 different ways:
1. Use the Council name (eg: `"Cowra Council"`)
2. Use the council component of the API url (eg: `"cowra"`)
3. User the full API url (eg: `"https://cowra.waste-info.com.au"`)

Currently supported councils and the argument options are given in the table below:

|#1: Council Name |#2: URL Component|#3: API URL|
|---|---|---|
|Baw Baw Shire Council|baw-baw|https://baw-baw.waste-info.com.au|
|Bayside Council|rockdale|https://rockdale.waste-info.com.au|
|Blue Mountains City Council|bmcc|https://bmcc.waste-info.com.au|
|Bega Valley Shire Council|bega|https://bega.waste-info.com.au|
|Brisbane City Council|brisbane|https://brisbane.waste-info.com.au|
|Burwood City Council|burwood|https://burwood.waste-info.com.au|
|Cowra Council|cowra|https://cowra.waste-info.com.au|
|Forbes Shire Council|forbes|https://forbes.waste-info.com.au|
|Gwydir Shire Council|gwydir|https://gwydir.waste-info.com.au|
|Lithgow City Council|lithgow|https://lithgow.waste-info.com.au|
|Livingstone Shire Council|livingstone|https://livingstone.waste-info.com.au|
|Moira Shire Council|moira|https://moira.waste-info.com.au|
|Moree Plains Shire Council|moree-waste|https://moree-waste.waste-info.com.au|
|Penrith City Council|penrith|https://penrith.waste-info.com.au|
|Port Macquarie Hastings Council|pmhc|https://pmhc.waste-info.com.au|
|Queanbeyan-Palerang Regional Council|qprc|https://qprc.waste-info.com.au|
|Singleton Council|singleton|https://singleton.waste-info.com.au|
|Snowy Valleys Council|snowy-valleys|https://snowy-valleys.waste-info.com.au|
|South Burnett Regional Council|sbrc|https://baw-sbrc.waste-info.com.au|
|Wellington Shire Council|wellington|https://wellington.waste-info.com.au|


**property_id**
*(integer) (optional)*\
The property id can be found by inspecting the network traffic when using the council's website to find the schedule.


OR

**suburb**
*(string) (optional)*\
It must match the suburb of the address available via the calendar provided on the council's website.

**street_name**
*(string) (optional)*\
It must match the street name of the address available via the calendar provided on the council's website.

**street_number**
*(string) (optional)*\
It must match the street number of the address available via the calendar provided on the council's website.


## Examples (different configurations, same address)

```yaml
waste_collection_schedule:
  sources:
    - name: impactapps_com_au
      args:
        service: "Penrith City Council"
        suburb: "Emu Plains"
        street_name: "Beach Street"
        street_number: "3"
```
```yaml
waste_collection_schedule:
  sources:
    - name: impactapps_com_au
      args:
        service: "penrith"
        property_id: "14122"
```
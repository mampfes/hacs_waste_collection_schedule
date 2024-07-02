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

1. Use one of the following known councils:
    - `Baw Baw Shire Council`
    - `Bayside City Council`
    - `Blue Mountains City Council`
    - `Bega Valley Shire Council`
    - `Burwood City Council`
    - `Cowra Council`
    - `Forbes Shire Council`
    - `Gwydir Shire Council`
    - `Lithgow City Council`
    - `Livingstone Shire Council`
    - `Loddon Shire Council`
    - `Moira Shire Council`
    - `Moree Plains Shire Council`
    - `Penrith City Council`
    - `Port Macquarie Hastings Council`
    - `Queanbeyan-Palerang Regional Council`
    - `Singleton Council`
    - `Snowy Valleys Council`
    - `South Burnett Regional Council`
    - `Wellington Shire Council`
1. Provide the api url for the council. For example:
    - `https://baw-baw.waste-info.com.au`
    - `https://bayside.waste-info.com.au`
1. Provide the council component of the url. For example:
    - `baw-baw`
    - `bayside`



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


## Example

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

# Min Renovasjon

This plugin is based on https://github.com/Danielhiversen/home_assistant_min_renovasjon

`street_code` and `county_id` needs to be looked up at kartverket:

 * Webgui: https://ws.geonorge.no/adresser/v1/#/default/get_sok
 * API: https://ws.geonorge.no/adresser/v1/sok?sok=Min%20Gate%2012

`street_code` equals to `adressekode` and `county_id` equals to `kommunenummer`.


```
waste_collection_schedule:
  sources:
    - name: minrenovasjon_no
      args:
        street_name: "Rådhustorget"
        house_number: "2"
        street_code: "2469"
        county_id: "3024"
```


```
sensor:
  - platform: waste_collection_schedule
    name: renovasjon
    details_format: generic
```

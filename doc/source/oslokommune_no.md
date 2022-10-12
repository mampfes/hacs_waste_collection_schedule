# Oslo Kommune

`street_id` needs to be looked up at kartverket:

- Webgui: https://ws.geonorge.no/adresser/v1/#/default/get_sok
- API: https://ws.geonorge.no/adresser/v1/sok?sok=Min%20Gate%2012

`street_code` equals to `adressekode` and `county_id` equals to `kommunenummer`.

```yaml
waste_collection_schedule:
  sources:
    - name: oslokommune_no
      args:
        street_name: ""
        house_number: ""
        house_letter: ""
        street_id: ""
```

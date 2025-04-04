# Oslo Kommune

`street_id` needs to be looked up at kartverket:

- Web UI: https://ws.geonorge.no/adresser/v1/#/default/get_sok
- API: https://ws.geonorge.no/adresser/v1/sok?sok=Min%20Gate%2012

`street_id` is equal to `adressekode`.

```yaml
waste_collection_schedule:
  sources:
    - name: oslokommune_no
      args:
        street_name: ""
        house_number: ""
        house_letter: ""
        street_id: ""
        point_id: ""
```

## Filter waste pickup point

Some addresses have multiple waste pickup points available. In this case you can optionally set `point_id` to only see a specific pickup point associated with your address.

Search your address in the web UI:
https://www.oslo.kommune.no/avfall-og-gjenvinning/nar-hentes-avfallet/

Scroll down to see the pickup points in a map. Note the name of the pickup point you prefer.

Finding the point ID can be a bit tricky as you need to manually go to the API URL and replace the URL parameters:
<https://www.oslo.kommune.no/xmlhttprequest.php?service=ren.search&street=Nåkkves%20Vei&number=5&street_id=15280>

In the JSON result, you need to find the item in `HentePunkts` that corresponds with the name in the web UI and use its `Id` field as your `point_id`.

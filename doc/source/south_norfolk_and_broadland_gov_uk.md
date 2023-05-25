# South Norfolk and Broadland Council

Support for schedules provided by [South Norfolk and Broadland Council](https://www.southnorfolkandbroadland.gov.uk/rubbish/find-bin-collection-day)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: south_norfolk_and_broadland_gov_uk
      args:
        address_payload: ADDRESS_PAYLOAD
```

Full examples for both council areas are given at the bottom of the documentation.

### Configuration Variables

**address_payload**<br/>
*(dict) (required)*

This is the only configuration variable and is required. It is very easy to fetch by capturing the data from a cookie using Google Chrome or a Chromium-based browser. (This method does not work in Firefox or Safari).
1. Go to https://area.southnorfolkandbroadland.gov.uk/
2. Input your postcode and select your address
3. Paste the following code snippet into your browser console (right click -> inspect element -> console)
4. Paste the result into your `configuration.yaml`

```js
cookieStore.get("MyArea.Data")
    .then(({ value }) => value)
    .then(decodeURIComponent)
    .then(JSON.parse)
    .then((value) => JSON.stringify(value, null, 2))
    .then(console.log)
    .catch(console.error);
```

## Example (for an address in Broadland)

```yaml
waste_collection_schedule:
  sources:
    - name: south_norfolk_and_broadland_gov_uk
      args:
        address_payload: {
            "Uprn": "010014355477",
            "Address": "29 Mallard Way, Sprowston, Norwich, Norfolk, NR7 8DN",
            "X": "626227.00000",
            "Y": "312136.00000",
            "Ward": "Sprowston East",
            "Parish": "Sprowston",
            "Village": "Sprowston",
            "Street": "Mallard Way",
            "Authority": "2610"
          }
```

## Example (for an address in South Norfolk)

```yaml
waste_collection_schedule:
  sources:
    - name: south_norfolk_and_broadland_gov_uk
      args:
        address_payload: {
            "Uprn": "002630148121",
            "Address": "14 Fairland Street, Wymondham, Norfolk, NR18 0AW",
            "X": "611129.00000",
            "Y": "301398.00000",
            "Ward": "Central Wymondham",
            "Parish": "Wymondham",
            "Village": "Wymondham",
            "Street": "Fairland Street",
            "Authority": "2630"
          }
```

# South Norfolk and Broadland Council

Support for schedules provided by [South Norfolk and Broadland Council](https://www.southnorfolkandbroadland.gov.uk/rubbish/find-bin-collection-day) (the joint operations of South Norfolk Council and Broadland District Council).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: south_norfolk_and_broadland_gov_uk
      args:
        postcode: POSTCODE
        address: ADDRESS
        address_payload: ADDRESS_PAYLOAD ## Deprecated
```

Full examples for both council areas are given at the bottom of the documentation.

### Configuration Variables

**postcode**  
*(String) (optional)  

**address**  
*(String) (optional)  

**address_payload**  
*(dict) (optional) (depreated)*  

Either address_payload or postcode and address are needed (address_payload will be used if both are present).

## Get the arguments

### postcode and address

- Go to <https://area.southnorfolkandbroadland.gov.uk/FindAddress>.
- Enter your postcode and also use it as postcode variable.
- Select your address and use it as address variable. The configured string should exactly match the text of your selection in the dropdown.

### address_payload (depricated)

This argument is the old way of configuring this source, and using it overrides any arguments given for postcode and address. It is easy to fetch by capturing the data from a cookie using Google Chrome or a Chromium-based browser (e.g. Edge). If you are using another browser (such as Firefox or Safari), please use the postcode and address arguments instead as this method will not work.
1. Go to https://area.southnorfolkandbroadland.gov.uk/
2. Input your postcode and select your address
3. Open your browser's console (right click -> Inspect Element -> Console)
4. Paste the following code snippet into the console
5. Paste the result into your `configuration.yaml`

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
        address: 29 Mallard Way, Sprowston, Norfolk, NR7 8DN
        postcode: NR7 8DN
```

or

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
        address: 14 Fairland Street, Wymondham, Norfolk, NR18 0AW
        postcode: NR18 0AW
```

or

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

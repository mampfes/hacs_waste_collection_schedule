# South Norfolk and Broadland Council

Support for schedules provided by [South Norfolk and Broadland Council](https://www.southnorfolkandbroadland.gov.uk/rubbish/find-bin-collection-day)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: south_norfolk_gov_uk
    - args:
      address_payload: ADDRESS_PAYLOAD
```

### Configuration Variables

**address_payload**<br/>
*(dict) (required)*

This is the only configuration variable and is required. It is very easy to fetch.
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

## Example

```yaml
waste_collection_schedule:
  sources:
    - address_payload: {
        "Uprn": "100091575309",
        "Address": "Tesco Stores Ltd, Blue Boar Lane, Sprowston, Norwich, Norfolk, NR7 8AB",
        "X": "625657.00000",
        "Y": "312146.00000",
        "Ward": "Sprowston East",
        "Parish": "Sprowston",
        "Village": "Sprowston",
        "Street": "Blue Boar Lane",
        "Authority": "2610"
      }
```

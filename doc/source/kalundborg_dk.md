# Kalundborg Kommune

Support for schedules provided by [Kalundborg Kommune](https://kalundborg.dk/), serving Kalundborg municipality, Denmark.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: kalundborg_dk
      args:
        id: See description
```

### Configuration Variables

**id**  
_(String) (required)_

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: kalundborg_dk
      args:
        id: "00006ac8-0002-0001-4164-647265737320"
```

## How to get the id

    To get your UUID (Geolocation) ID:
    1. Go to the [Kalundborg Kommune Min Side](https://kalundborg.dk/) page and navigate to waste collection services. 
    2. or go directly to : https://kalundborg.infovision.dk/public/selectaddress
    3. Search for your address.
    4. You will find your ID in URL i.e. : https://kalundborg.infovision.dk/public/address/00006ac8-0002-0001-4164-647265737320
    5. The ID should be a UUID format like: `00006ac8-0002-0001-4164-647265737320`

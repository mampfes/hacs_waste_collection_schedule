# Geovest

Support for schedules provided by [Geovest](https://geovest.bluemilk.dev).

Source for Geovest, Italy.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: geovest_it
      args:
        address_name: ADDRESS_NAME
        town_id: TOWN_ID
        numbers: NUMBERS
        calendar_type_id: CALENDAR_TYPE_ID
        days: DAYS
        device_id: DEVICE_ID
        authorization: AUTHORIZATION
```

### Configuration Variables

**address_name**  
*(string) (required)*

**town_id**  
*(string) (required)*

**numbers**  
*(string) (optional)*

**calendar_type_id**  
*(string) (optional)*

**days**  
*(string) (optional)*

**device_id**  
*(string) (optional)*

**authorization**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: geovest_it
      args:
        town_id: '7'
        numbers: '228'
        address_name: via gramsci
        device_id: '1111111111111111'
```

## How to get the source arguments

Choose your town id from the Geovest list, then search your street name. The house number defaults to 1 and is only used when several streets match. A device id is generated when you leave it empty. Replace the authorization token only if the built-in one stops working. Calendar type 1 is a private address and 2 is a business.

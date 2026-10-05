# WSZ Moosburg

Support for schedules provided by [WSZ Moosburg](https://wsz-moosburg.at).

Source for WSZ Moosburg/Kärnten, including Moosburg, Pörtschach, Techelsberg

## Configuration via configuration.yaml

### Using address_id

```yaml
waste_collection_schedule:
  sources:
    - name: wsz_moosburg_at
      args:
        address_id: ADDRESS_ID
```

### Using municipal, address and street

```yaml
waste_collection_schedule:
  sources:
    - name: wsz_moosburg_at
      args:
        municipal: MUNICIPAL
        address: ADDRESS
        street: STREET
```

### Configuration Variables

**address_id**  
*(string) (alternative)*

**municipal**  
*(string) (alternative)*

**address**  
*(string) (alternative)*

**street**  
*(string) (alternative)*

Provide one of: `address_id` or `municipal` + `address` + `street`.

## Example

### Using address_id

```yaml
waste_collection_schedule:
  sources:
    - name: wsz_moosburg_at
      args:
        address_id: 70265
```

### Using municipal, address and street

```yaml
waste_collection_schedule:
  sources:
    - name: wsz_moosburg_at
      args:
        municipal: Moosburg
        address: "Oberg\xF6riach"
        street: "Oberg\xF6riach"
```

## How to get the source arguments

Pick your municipality, then your address and, where the address has several streets, the street. Alternatively enter the address ID directly: it is the number in the request https://wsz-moosburg.at/api/trash/<ID> that the calendar on wsz-moosburg.at makes for your address.

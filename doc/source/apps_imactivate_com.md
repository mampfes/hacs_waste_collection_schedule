# Apps by imactivate

Support for schedules provided by [Apps by imactivate](https://imactivate.com), serving multiple, UK.

Known to work with:

- Leads Bins (<https://play.google.com/store/apps/details?id=com.imactivate.bins>)
- Rotherham Bins (<https://play.google.com/store/apps/details?id=com.imactivate.rotherhambinsrelease>)
- Luton Bins (<https://play.google.com/store/apps/details?id=com.imactivate.lutonbins>)
- Fenland Bins (<https://play.google.com/store/apps/details?id=com.imactivate.fenlandbins>)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: apps_imactivate_com
      args:
        postcode: POSTCODE
        town: TOWN
        street: STREET
        number: "NUMBER"        
```

### Configuration Variables

**postcode**  
*(String) (required)*

**town**  
*(String) (required)*

**street**  
*(String) (required)*

**number**  
*(String | Integer) (required)*

## Example

### Leads

```yaml
waste_collection_schedule:
    sources:
    - name: apps_imactivate_com
      args:
        postcode: LS6 2SE
        town: Leeds
        street: sharp mews
        number: 2
```

### Fenland

```yaml
waste_collection_schedule:
    sources:
    - name: apps_imactivate_com
      args:
        postcode: PE158RD
        town: March
        street: Creek Road
        number: "90"        
```

## How to get the source argument

Find the parameter of your address using []() and write them exactly like on the web page.

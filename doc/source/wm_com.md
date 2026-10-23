# Waste Management (WM)

Support for schedules provided by [Waste Management (WM)](https://www.wm.com).

Source for Waste Management (wm.com) residential pickup schedules using the guest address lookup — no account required.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: wm_com
      args:
        street: STREET
        city: CITY
        state: STATE
        zip_code: ZIP_CODE
        country: COUNTRY
```

### Configuration Variables

**street**  
*(string) (required)*

**city**  
*(string) (required)*

**state**  
*(string) (required)*

**zip_code**  
*(string) (required)*

**country**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: wm_com
      args:
        street: 245 Emerson Ave
        city: Ypsilanti
        state: MI
        zip_code: '48198'
```

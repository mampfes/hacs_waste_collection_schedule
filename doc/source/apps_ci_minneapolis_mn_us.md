# apps_ci_minneapolis_mn_us

Support for schedules provided by [The City of Minnneapolis](https://apps.ci.minneapolis.mn.us/AddressPortalApp/Search?AppID=RecycleFinderApp)


## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: apps_ci_minneapolis_mn_us
      args:
        apn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**apn**  
*(string) (required)*


## Example

```yaml
waste_collection_schedule:
  sources:
    - name: apps_ci_minneapolis_mn_us
      args:
        apn: 2302924330044
```

# Kiedy śmieci

Support for schedules provided by [Kiedy śmieci](https://kiedysmieci.info/), serving multiple municipalities, Poland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kiedysmieci_info
      args:
        voivodeship: voivodeship (województwo)
        district: district (powiat)
        municipality: municipality (gmina)
        street: street (ulica)
        
```

### Configuration Variables

**voivodeship**
*(String) (required)*

**district**
*(String) (required)*

**municipality**
*(String) (required)*

**street**
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: kiedysmieci_info
      args:
        voivodeship: podkarpackie
        district: sanocki
        municipality: Bukowsko
        street: Nadolany
```

## How to get the source argument

The parameters can be found by using the apps ([GooglePlay](https://play.google.com/store/apps/details?id=com.fxsystems.KiedySmieci_info), [AppStore](https://apps.apple.com/pl/app/kiedy-%C5%9Bmieci/id1539957094?l=pl)) or on the [website](https://kiedysmieci.info/index.html#harmonogram) by providing your municipality in the search form.
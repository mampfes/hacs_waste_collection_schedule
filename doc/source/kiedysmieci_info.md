# Kiedy śmieci

Support for schedules provided by [Kiedy śmieci](https://kiedysmieci.info).

Source script for Kiedy śmieci, Poland

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kiedysmieci_info
      args:
        voivodeship: VOIVODESHIP
        district: DISTRICT
        municipality: MUNICIPALITY
        street: STREET
```

### Configuration Variables

**voivodeship**  
*(string) (optional)*

**district**  
*(string) (optional)*

**municipality**  
*(string) (optional)*

**street**  
*(string) (optional)*

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

## How to get the source arguments

Setting this source up through the Home Assistant UI needs no lookup: the wizard asks for the voivodeship (województwo), district (powiat), municipality (gmina) and street or locality (ulica) one at a time, and each dropdown lists what the provider returns for the levels already chosen. For configuration.yaml, the same values can be read off the apps ([GooglePlay](https://play.google.com/store/apps/details?id=com.fxsystems.KiedySmieci_info), [AppStore](https://apps.apple.com/pl/app/kiedy-%C5%9Bmieci/id1539957094?l=pl)) or the [website](https://kiedysmieci.info/index.html#harmonogram).

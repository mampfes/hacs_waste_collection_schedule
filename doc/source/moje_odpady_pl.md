# App Moje Odpady

Support for schedules provided by [App Moje Odpady](https://moje-odpady.pl/), serving multiple municipalities, Poland.

<https://play.google.com/store/apps/details?id=com.mojeodpady>

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: moje_odpady_pl
      args:
        city: CITY
        voivodeship: VPICODESHIP (województwo)
        
```

### Configuration Variables

**city**  
*(String) (required)*

**voivodeship**  
*(String) (optional)* needed if there are multiple cities with the same name

**address**  
*(String) (optional)* only needed if the app asks for an address

**house_number**  
*(String) (optional)* rarely needed, only if the app asks for a house number

**english**  
*(String) (optional)* if set to "true" the app will return the schedule in English

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: moje_odpady_pl
      args:
        city: Aleksandrów
        voivodeship: woj. śląskie
        english: False # optional parameter
```

```yaml
waste_collection_schedule:
    sources:
    - name: moje_odpady_pl
      args:
        city: BASZKÓWKA
        voivodeship: woj. mazowieckie
        address: ANTONÓWKI
        house_number: Pozostałe
        english: False # optional parameter
```

## How to get the source argument

The parameters can be found by using the app ([GooglePlay](https://play.google.com/store/apps/details?id=com.mojeodpady&hl=pl), [AppStore](https://apps.apple.com/pl/app/waste-collection-schedule/id1248697353)) and checking the address input form.

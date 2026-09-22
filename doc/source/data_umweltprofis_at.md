# Umweltprofis

Support for schedules provided by [Umweltprofis](https://www.umweltprofis.at).

Source for Umweltprofis

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: data_umweltprofis_at
      args:
        district: DISTRICT
        city: CITY
        street: STREET
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**district**  
*(string) (required)*

**city**  
*(string) (required)*

**street**  
*(string) (required)*

**house_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: data_umweltprofis_at
      args:
        district: Rohrbach
        city: "Aigen-Schl\xE4gl"
        street: Almesbergerweg
        house_number: '1'
```

## How to get the source arguments

Enter your address exactly as it is offered at https://www.umweltprofis.at/allgemein/module/wann_wird_mein_abfall_abgeholt.html: district (Bezirk), municipality, street and house number. Where a type is offered at several intervals (for example Restabfall 2- or 4-weekly), the first one the page lists is used.

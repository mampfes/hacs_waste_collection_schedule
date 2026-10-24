# Gliwice

Support for schedules provided by [Gliwice](https://segreguj.gliwice.eu).

Source for single-family housing waste collection in Gliwice, Poland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: segreguj_gliwice_eu
      args:
        street: STREET
```

### Configuration Variables

**street**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: segreguj_gliwice_eu
      args:
        street: Agrestowa
```

## How to get the source arguments

Enter your street exactly as listed in the single-family housing schedule (Harmonogram_Gliwice_Zabudowa_Jednorodzina) on https://segreguj.gliwice.eu/harmonogram-wywozu-pliki-do-pobrania/. Streets split by house number are listed once per range, e.g. 'Rolników od nr 237 nieparzyste'; enter the whole entry.

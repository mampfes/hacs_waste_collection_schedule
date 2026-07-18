# Ecoharmonogram

Support for schedules provided by [Ecoharmonogram](https://ecoharmonogram.pl).

Source for ecoharmonogram.pl

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ecoharmonogram_pl
      args:
        town: TOWN
        street: STREET
        house_number: HOUSE_NUMBER
        district: DISTRICT
        additional_sides_matcher: ADDITIONAL_SIDES_MATCHER
        community: COMMUNITY
        app: APP
        language: LANGUAGE
        g1: G1
        g2: G2
        g3: G3
        g4: G4
        g5: G5
```

### Configuration Variables

**town**  
*(string) (required)*

**street**  
*(string) (optional)*

**house_number**  
*(string) (required)*

**district**  
*(string) (optional)*

**additional_sides_matcher**  
*(string) (optional)*

**community**  
*(string) (optional)*

**app**  
*(string) (optional)*

**language**  
*(string) (optional)*

**g1**  
*(string) (optional)*

**g2**  
*(string) (optional)*

**g3**  
*(string) (optional)*

**g4**  
*(string) (optional)*

**g5**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ecoharmonogram_pl
      args:
        town: "Cz\u0119stochowa"
        street: Bartnicza
        house_number: '9'
        district: "Cz\u0119stochowa"
        additional_sides_matcher: "Szk\u0142o (1 x miesi\u0105c)"
        g1: "Firmy (5 fakcji + popi\xF3\u0142 2,3,4 x mc)"
        g2: "Zmieszane (5 x miesi\u0105c)"
        g3: "Bio (3 x miesi\u0105c)"
        g4: "Metale i Tworzywa (4 x miesi\u0105c)"
        g5: "Papier (1 x miesi\u0105c)"
```

## How to get the source arguments

Fill in Town, Street, House number and District and press confirm. If any other field is required, the error will list the available options as suggestions. If your Town is not found, you might need to provide the App argument (see the linked documentation below for a list of towns with their corresponding App argument).

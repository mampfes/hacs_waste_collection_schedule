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
        region: REGION
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

**region**  
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
        app: legnica
        town: Legnica
        street: Bieszczadzka
        house_number: '27'
```

## How to get the source arguments

Fill in Town, Street, House number and District and press confirm. If any other field is required, the error will list the available options as suggestions. If your Town is not found, you might need to provide the App argument (see the linked documentation below for a list of towns with their corresponding App argument). For Legnica, select the Legnica provider or set App to legnica.

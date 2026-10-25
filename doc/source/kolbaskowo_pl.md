# Gmina Kołbaskowo

Support for schedules provided by [Gmina Kołbaskowo](https://kolbaskowo.pl).

Source for Gmina Kołbaskowo, Poland (single-family housing).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kolbaskowo_pl
      args:
        district: DISTRICT
        street: STREET
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**district**  
*(string) (required)*

**street**  
*(string) (optional)*

**house_number**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: kolbaskowo_pl
      args:
        district: "Kur\xF3w"
```

## How to get the source arguments

Enter your village as named on https://kolbaskowo.pl/harmonogramy-odbioru-odpadow-dla-zabudowy-jednorodzinnej.html (e.g. 'Kurów' or 'Kołbaskowo'). 'Kurów' is the schedule for the village except ul. Na Klifie and ul. Wichrowe Wzgórza; set street to one of those (e.g. 'Na Klifie') for their file. For Będargowo 50-57, Siadło Dolne 32, 32a or 34-63, or Stobno 52-54 (Małe Stobno), also enter the house number. You can instead paste the full link title. This covers single-family housing only.

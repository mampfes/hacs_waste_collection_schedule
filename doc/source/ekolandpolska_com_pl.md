# Ekoland Polska (Kraśnik area)

Support for schedules provided by [Ekoland Polska (Kraśnik area)](https://www.ekolandpolska.com.pl).

Source for Ekoland Polska waste collection in the Kraśnik area, Poland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ekolandpolska_com_pl
      args:
        municipality: MUNICIPALITY
        street: STREET
```

### Configuration Variables

**municipality**  
*(string) (required)*

**street**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ekolandpolska_com_pl
      args:
        municipality: "Miasto Kra\u015Bnik"
        street: Lubelska
```

## How to get the source arguments

Enter your municipality ('Miasto Kraśnik', 'Gmina Kraśnik', 'Dzierzkowice', 'Gościeradów', 'Trzydnik Duży' or 'Wilkołaz') and your street or village as printed in the schedule PDF linked on https://www.ekolandpolska.com.pl/dla-mieszkancow/odbior-odpadow-gminy (e.g. 'Lubelska' or 'Lasy'). Accents and case are ignored. Only detached houses (zabudowa jednorodzinna) are supported.

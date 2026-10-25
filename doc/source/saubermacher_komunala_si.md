# Saubermacher - Komunala

Support for schedules provided by [Saubermacher - Komunala](https://www.saubermacher-komunala.si).

Source for Saubermacher - Komunala (Murska Sobota and Pomurje municipalities), Slovenia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: saubermacher_komunala_si
      args:
        municipality: MUNICIPALITY
        district: DISTRICT
```

### Configuration Variables

**municipality**  
*(string) (required)*

**district**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: saubermacher_komunala_si
      args:
        municipality: Murska Sobota
        district: Murska Sobota - rajon 4
```

## How to get the source arguments

Choose your municipality, then enter your settlement exactly as its calendar is named under 'Urniki odvozov' on the municipality's page at https://www.saubermacher-komunala.si/kje-zbiramo-odpadke (e.g. 'Bogojina'). In Murska Sobota town use your district without the weekday, e.g. 'Murska Sobota - rajon 4' or 'Murska Sobota - bloki'; the PDF 'Razdelitev mesta Murska Sobota na rajone' shows the districts.

# Fleurieu Regional Waste Authority

Support for schedules provided by [Fleurieu Regional Waste Authority](https://fleurieuregionalwasteauthority.com.au), serving the following regions of the Fleurieu Peninsula, Southern Australia:
 - [Kangaroo Island Council](https://www.kangarooisland.sa.gov.au)
 - [District Council of Yankalilla](https://www.yankalilla.sa.gov.au)
 - [City of Victor Harbor](https://www.victor.sa.gov.au)
 - [Alexandrina Council](https://www.alexandrina.sa.gov.au)


## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: frwa_com_au
      args:
        name_or_number: NAME_OR_NUMBER
        street: STREET
        district: DISTRICT
```

### Configuration Variables

**name_or_number**  
*(Integer | String) (required)*
The number or name of the property, as displayed on the FRWA web site


**street**  
*(String) (required)*
The street name of the property, as displayed on the FRWA web site

**address**  
*(String) (required)*
The district name of the property, as displayed on the FRWA web site

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: frwa_com_au
      args:
        name_or_number: 42
        street: Wishart Crescent
        district: Encounter Bay
```

## How to get the source arguments

Visit https://fleurieuregionalwasteauthority.com.au/collection-calendar-downloads and search for your address. Use the name/number, street name and district name as they appear when your collection schedule in being displayed.

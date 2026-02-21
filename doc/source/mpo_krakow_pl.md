# MPO Kraków

Support for schedules provided by [MPO Kraków](https://harmonogram.mpo.krakow.pl/), serving Kraków, Poland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: mpo_krakow_pl
      args:
        street_name: Street (Ulica)
        building_number: Number (Numer)
        
```

### Configuration Variables

**street_name**  
*(String) (required)*	To obtain the street name, please visit <https://harmonogram.mpo.krakow.pl> 

**building_number**  
*(String) (required)*   To obtain the building number, please visit <https://harmonogram.mpo.krakow.pl> 

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: mpo_krakow_pl
      args:
        street_name: Romanowicza
        building_number: 1 DM
        
```

## How to get the source argument

You can check your parameters at <https://harmonogram.mpo.krakow.pl> and write them exactly like suggested on the web page.

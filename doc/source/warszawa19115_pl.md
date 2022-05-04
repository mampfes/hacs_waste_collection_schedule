# Warszawa19115

Support for schedules provided by [Warszawa19115](https://warszawa19115.pl/harmonogramy-wywozu-odpadow).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: warszawa19115_pl
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address**<br>
*(string) (optional)*

**geolocation_id**<br>
*(string) (optional)*

At least one argument must be provided.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: warszawa19115_pl
      args:
        street_address: MARSZAŁKOWSKA 84/92, 00-514 Śródmieście
```

```yaml
waste_collection_schedule:
  sources:
    - name: warszawa19115_pl
      args:
        geolocation_id: 76802934
```

## How to get the source arguments

Visit the [Warszawa19115 - Harmonogram odbioru odpadów](https://warszawa19115.pl/harmonogramy-wywozu-odpadow) page and search for your address. The ```street_address``` argument should exactly match the street address shown in the autocomplete result. For unlisted addresses use an adjacent listed address.

The ```geolocation_id``` argument can be used to bypass the initial address lookup on first use. This value can be discovered using the developer console in any modern browser and inspecting the request sent once an address is selected and the search button is clicked. The request URL takes the format: ```https://warszawa19115.pl/harmonogramy-wywozu-odpadow?p_p_id=portalCKMjunkschedules_WAR_portalCKMjunkschedulesportlet_INSTANCE_o5AIb2mimbRJ&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_resource_id=ajaxResourceURL&p_p_cacheability=cacheLevelPage&p_p_col_id=column-1&p_p_col_count=1```.

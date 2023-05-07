# Jumomind.de / MyMuell.de

Support for schedules provided by [jumomind.de](https://jumomind.de/) and [MyMüll App](https://www.mymuell.de). Jumomind and MyMüll are services provided by [junker.digital](https://junker.digital/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: jumomind_de
      args:
        service_id: SERVICE_ID
        city: CITY
        street: STREET
        house_number: HOUSE NUMBER
        city_id: CITY_ID # deprecated
        area_id: AREA_ID # deprecated
```

### Configuration Variables

**service_id**  
*(string) (required)*

**city**  
*(string) (required)*

**street**  
*(string) (optional)*  
Not needed for all providers or cities

**house_number**  
*(string) (optional)*  
Not needed for all providers, cities or streets

**city_id**  
*(string) (optional)* (deprecated)*

**area_id**  
*(string) (required)* (deprecated)*

## Example

### ZAW

```yaml
waste_collection_schedule:
  sources:
    - name: jumomind_de
      args:
        service_id: zaw
        city: Alsbach-Hähnlein
        street: Hauptstr.
```

### MyMuell

#### Without street

```yaml
waste_collection_schedule:
  sources:
    - name: jumomind_de
      args:
        service_id: mymuell
        city: Kipfenberg OT Arnsberg, Biberg, Dunsdorf, Schelldorf, Schambach, Mühlen im Schambachtal und Schambacher Leite, Järgerweg, Böllermühlstraße, Attenzell, Krut, Böhming, Regelmannsbrunn, Hirnstetten und Pfahldorf
```

#### With street

```yaml
waste_collection_schedule:
  sources:
    - name: jumomind_de
      args:
        service_id: mymuell
        city: Darmstadt
        street: Adolf-Spieß-Straße 2-8 # Housenumber is part of street so it is not in house_number
```

### Deprecated

```yaml
waste_collection_schedule:
  sources:
    - name: jumomind_de
      args:
        service_id: zaw
        city_id: 106
        area_id: 94
```

## How to get the source arguments

### New Version With Names

get your `service_id` from the list above.

#### For MyMuell services

Configure your `city`, `street`, `house_number` with the [https://www.mymuell.de](MyMüll.de App). The use a `city` from the list above or (if outedated) a selectable city from the app (can also be something like `Kipfenberg OT Arnsberg, Biberg, Dunsdorf, Schelldorf, Schambach, Mühlen im Schambachtal und Schambacher Leite, Järgerweg, Böllermühlstraße, Attenzell, Krut, Böhming, Regelmannsbrunn, Hirnstetten und Pfahldorf`) `street` and `house_number` is only needed if you get asked by the MyMüll App to provide one. If the house number is part of the street selecter it needs to be part of the street variable if the house number has its own selecter it should be in the `house_number` variable

#### for not MyMuell services

Use `city`, `street` and `house_number` argument from your providers' web page (Write them exactly like on the web page. Spelling errors may lead to errors). Note `city` argument is mandatory `street` and `house_number` are only required if your provider asks for them on their interactive web page.

### Deprecated Version With ids from terminal wizzard (Still works)

There is a script with an interactive command line interface which generates the required source configuration:

[https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/jumomind_de.py](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/jumomind_de.py).

First, install the Python module `inquirer`. Then run this script from a shell and answer the questions.

# Samverkan Återvinning Miljö (SÅM)

Support for schedules provided by [Samverkan Återvinning Miljö (SÅM)](https://samiljo.se/avfallshamtning/hamtningskalender/), serving the municipality of Gislaved, Gnosjö, Vaggeryd and Värnamo, Sweden. 

Helgvecka means that the pickup day might deviate from the scheduled day due to a public holiday during the week.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: samiljo_se
      args:
        street: STREET_NAME
        city: CITY_NAME
```

### Configuration Variables

**street**
*(string) (required)*

**city**
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: samiljo_se
      args:
        street: Storgatan 1
        city: Burseryd
```


## How to get the source argument

The source argument is the street including number and the city to the house with waste collection.
The address can be tested [here](https://samiljo.se/avfallshamtning/hamtningskalender/).

## How to add new waste types

If your address are missing any waste types that shows in the [Hämtningskalender](https://samiljo.se/avfallshamtning/hamtningskalender/). Then there might be missing mappings in the NAME_MAP. 
1. Run Samiljo_se_wastetype_searcher.py for the specific address or without arguments to scan all addresses in the database.  <br />
Examples of valid command below.
```shell
> samiljo_se_wastetype_searcher.py --street "Storgatan 1" --city "Burseryd"
> samiljo_se_wastetype_searcher.py --city "Burseryd"
> samiljo_se_wastetype_searcher.py --street "Storgatan 1"
> samiljo_se_wastetype_searcher.py
```
2. Missing mappings will be returned together with an address.
3. Use the [Hämtningskalender](https://samiljo.se/avfallshamtning/hamtningskalender/) to extract the corresponding common name to the new wastetype.
4. Add the new types to the NAME_MAP and optionaly to the ICON_MAP in samiljo_se.py and samiljo_se_wastetype_searcher.py.

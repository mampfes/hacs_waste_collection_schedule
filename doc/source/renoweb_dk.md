# Renoweb

Support for schedules provided by Sweco's [RenoWeb](https://renoweb.dk/), serving many Danish municipalities.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
        - name: renoweb_dk
          args:
              municipality: MUNICIPALITY
              address: ADDRESS
              address_id: ADDRESS_ID
```

### Configuration Variables

**municipality**  
_(String) (required)_

The name of the municipality as it appears in the URL. E.g. https://htk.renoweb.dk/Legacy/selvbetjening/mit_affald.aspx where "htk" is for Høje-Taastrup municipality.

**address**
_(String) (optional)_

The address to look up. It should be exactly as it is on the website until the comma between the street address and the postal code.

**address_id**
_(Int) (optional)_

Use address_id if the address lookup fails.

_Note that while both **address** and **address_id** are optional, one of them must be supplied and if both are used, **address_id** will take precedence._

## Example

```yaml
waste_collection_schedule:
    sources:
        - name: renoweb_dk
          args:
              municipality: frederiksberg
              address: "Roskildevej 40"
          customize:
              - type: "Haveaffald - Haveaffald henteordning (1 stk.)"
                alias: "Haveaffald"
```

## How to find the address_id

Go to the RenoWeb site for your municipality, e.g. https://htk.renoweb.dk/Legacy/selvbetjening/mit_affald.aspx if you are lucky enough to live in Høje-Taastrup.

Open the developer console in your browser.

Enter your address and select it in the dropdown menu. (Note that the Ejd.nr. in the dropdown is _not_ the ID we are looking for).

In the Network tab in the browser console, find the latest URL ending in **Adresse_SearchByString** and look in under Response, where you should see a chunk of JSON-ish data. The ID you need to use for adress_id is in the "value" field.

```json
d: '{"list":[{"value":"45149","label":"Rådhusstræde 1, 2630 Taastrup (Ejd.nr. 186783)"}],"status":{"id":0,"status":"Ok","msg":""}}'
```

### Customizing Waste Types

Customizing waste types is a feature of the Waste Collection Schedule component and is very useful here, since the waste types in RenoWeb are often long and not very consistent.

```yaml
waste_collection_schedule:
    sources:
        - name: renoweb_dk
          args:
              municipality: frederiksberg
              address: "Roskildevej 40"
          customize:
              - type: "Haveaffald - Haveaffald henteordning (1 stk.)"
                alias: "Haveaffald"
```

# Renoweb

Support for schedules provided by Sweco's [RenoWeb](https://renoweb.dk/), for the Danish municipalities that are still served by RenoWeb's public API.

> **Note:** RenoWeb's old "Legacy" website API now requires a MitID login and can no longer be used by this integration (see [issue #4084](https://github.com/mampfes/hacs_waste_collection_schedule/issues/4084)). This source instead uses the public API used by RenoWeb's own "Mit Affald" app, which does not require any login, but which only a subset of former RenoWeb municipalities are still served by — many municipalities have since moved their waste collection system to a different vendor entirely (most commonly "Perfect Waste"), which isn't supported by this source.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
        - name: renoweb_dk
          args:
              municipality: MUNICIPALITY
              address: ADDRESS
```

### Configuration Variables

**municipality**
_(String) (required)_

The name of the municipality. Currently supported: Aabenraa, Aalborg, Billund, Bornholm, Brøndby, Brønderslev, Dragør, Egedal, Esbjerg, Fredensborg, Gentofte, Glostrup, Hjørring, Jammerbugt, Kerteminde, Mariagerfjord, Randers, Rødovre, Samsø, Svendborg, Sønderborg, Varde, Vordingborg.

If your municipality isn't in this list, it is most likely no longer served by RenoWeb and this source won't work for you.

**address**
_(String) (required)_

The street name and house number, e.g. `"Torvegade 3"` or `"Torvegade 3, 6700 Esbjerg"`. Including the postal code helps disambiguate streets that exist more than once within the same municipality. A letter suffix (e.g. `"Torvegade 3A"`) is supported for addresses that need it.

## Example

```yaml
waste_collection_schedule:
    sources:
        - name: renoweb_dk
          args:
              municipality: Esbjerg
              address: "Torvegade 3, 6700 Esbjerg"
```

### Customizing Waste Types

Customizing waste types is a feature of the Waste Collection Schedule component and is very useful here, since the waste types in RenoWeb are often long and not very consistent.

```yaml
waste_collection_schedule:
    sources:
        - name: renoweb_dk
          args:
              municipality: Esbjerg
              address: "Torvegade 3, 6700 Esbjerg"
          customize:
              - type: "Haveaffald"
                alias: "Garden waste"
```

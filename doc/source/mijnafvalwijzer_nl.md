# Afval Wijzer

Afval Wijzer is no longer supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Visit <https://www.mijnafvalwijzer.nl> and search for your location to make sure it is recogniced
- Write down your postcode, house number and house number addition, if any (e.g. A)


### Configuration via yaml

```yaml
waste_collection_schedule:
  sources: 
    - name: mijnafvalwijzer_nl
      args:
        postcode: YOUR_POSTCODE
        number: HOUSE_NUMBER
        add: HOUSE_NUMBER_ADDITION
```

**Configuration Variables**

**postcode** _(string) (required)_ : Postcode of your property (e.g. 5014NN)
**postcode** _(string) (required)_ : House number (e.g. 174)
**add** _(string)_ : House number addition (e.g. A)

Example: Hoefstraat 174, Tilburg

```yaml
waste_collection_schedule:
  sources: 
    - name: mijnafvalwijzer_nl
      args:
        postcode: 5014NN
        number: 174
        add:
```

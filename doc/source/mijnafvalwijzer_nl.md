# Afval Wijzer

Afval Wijzer is a platform where users from many dutch municipalities can check their waste collection schedules.
Supported municipalities include, but are not limited to:
- Eindhoven
- Rotterdam
- Tilburg
- Midden-Groningen
- Waalwijk
- Kampen
- Oirschoot
- Oss
- ...

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

# Irado

Irado is the waste collection company for several municipalities in the
Rotterdam region, including:

- Vlaardingen
- Schiedam
- Maassluis
- Capelle aan den IJssel
- Voorne aan Zee

## How to get the configuration arguments

- Visit <https://www.irado.nl/afvalkalender> and fill in your postcode and
  house number to make sure your address is recognized
- Write down your postcode, house number and house number suffix, if any
  (e.g. A)

### Configuration via yaml

```yaml
waste_collection_schedule:
  sources:
    - name: irado_nl
      args:
        postcode: YOUR_POSTCODE
        house_number: YOUR_HOUSE_NUMBER
        suffix: YOUR_HOUSE_NUMBER_SUFFIX
```

**Configuration Variables**

**postcode** _(string) (required)_ : Dutch postcode of your property, e.g. `3131VX`

**house_number** _(string) (required)_ : House number, e.g. `3`

**suffix** _(string)_ : Optional house number suffix/addition, e.g. `A`

Example:

```yaml
waste_collection_schedule:
  sources:
    - name: irado_nl
      args:
        postcode: 3137CN
        house_number: 2
        suffix: A
```

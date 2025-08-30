# Norra Åsbo Renhållnings AB (NÅRAB)

Support for schedules provided by [Nårab](https://www.narabtomningskalender.se), serving municipalities in the region of Skåne, Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: narab_se
      args:
        address: ADDRESS
        kundNr: CUSTOMER_NUMBER
```

### Configuration Variables

**address**
*(string) (required)*

**kundNr**
*(int) (optional)*


There are two config options:

- Supply only the `address` arg. The script tries to match you address within the results returned from the website. If more than one match is returned, the `kundNr` needs to be filled as well.
- Supply both the `address` and `kundNr` args. The `kundNr` arg uniquely identifies your property in the system. See below for how to identify your customer number.

## Example using `address` arg

```yaml
waste_collection_schedule:
    sources:
    - name: narab_se
      args:
        address: "16 Davy Close"
```

## Example using `kundNr` arg

```yaml
waste_collection_schedule:
    sources:
    - name: narab_se
      args:
        address: "Hallandsvägen 9"
        kundNr: 33159
```

## How to find your Customer Number

When viewing your collection schedule on the [Nårab](https://www.narabtomningskalender.se) web site. Inspect the page source and search for `narabKUNDNRData`. You should seem something like this:

`<input type="hidden" id="narabKUNDNRData" name="narabKUNDNRData" value="33035">`

The number in the _value_ attribute should be used as the `kundNr` arg.

Alternatively, you can run the [narab_se](/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/narab_se.py) wizard script. For a given address, it will list possible matches and associated customer number. For example:

```bash
Enter your address: Helsingborgsvägen
Helsingborgsvägen PERSTORP (Verksamhet) kundNr: 20862
Helsingborgsvägen 22 PERSTORP (Verksamhet) kundNr: 28749
Helsingborgsvägen 31 PERSTORP kundNr: 25494
Helsingborgsvägen 33 PERSTORP kundNr: 30193
Helsingborgsvägen 90 PERSTORP kundNr: 2979
```

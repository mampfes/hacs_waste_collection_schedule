# Moji odpadki

Support for schedules provided by JAVNO PODJETJE VODOVOD KANALIZACIJA SNAGA d.o.o., Ljubljana, Slovenia: [Moji odpadki](https://www.mojiodpadki.si/urniki/urniki-odvoza-odpadkov)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
      - name: mojiodpadki_si
        args:
          uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**uprn**  
*(string) (required)*

This is required to unambiguously identify the property.

## Example using UPRN

```yaml
waste_collection_schedule:
    sources:
      - name: mojiodpadki_si
        args:
          uprn: "1049"
```

## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to
<https://www.mojiodpadki.si/urniki/urniki-odvoza-odpadkov> and entering in your address details.

UPRN is the last component of the URL once the schedule is displayed.

Example:
- Address: Šubičeva ulica 4
- Schedule URL: `https://www.mojiodpadki.si/urniki/urniki-odvoza-odpadkov/s/1049`
- UPRN: 1049

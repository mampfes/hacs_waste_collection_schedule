# Čisto mesto - Slovenia

Support for schedules provided by [Čisto mesto Ptuj](https://cistomesto.si/), SI.

Čisto mesto Ptuj serves the Ptuj area and a number of surrounding municipalities. The schedule is read from the same backend the provider's mobile app uses.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: cistomesto_si
      args:
        region: REGION
```

### Configuration Variables

**region**</br>
*(string | integer) (required)*

The name of your municipality (for example `Majšperk`) or its numeric region ID (for example `107`).

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: cistomesto_si
      args:
        region: "Majšperk"
```

## How to get the source argument

`region` accepts either the municipality name as shown in the Čisto mesto app, or the numeric region ID.

The following municipality names are currently offered by the provider:

Cirkulane, Destrnik, Duplek, Duplek - Ostala naselja, Duplek - Ostala naselja bloki, Duplek - Zgornji Duplek, Duplek - Zgornji Duplek bloki, Gorišnica, Hajdina, Juršinci, Kidričevo, Kidričevo - Bloki, Majšperk, Markovci, Podlehnik, Sveti Andraž, Trnovska vas, Videm, Vitanje, Zavrč, Zreče, Žetale <!-- codespell:ignore -->

Some municipalities are split by the provider into more than one collection area that share the same name. If the schedule you get does not match your address, use the numeric region ID instead of the name to select the correct area.

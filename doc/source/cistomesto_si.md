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

```yaml
waste_collection_schedule:
    sources:
    - name: cistomesto_si
      args:
        region: 126
```

## How to get the source argument

`region` accepts either the municipality name as shown in the Čisto mesto app, or the numeric region ID.

The following municipality names are currently offered by the provider:

Cirkulane, Destrnik, Duplek, Duplek - Ostala naselja, Duplek - Ostala naselja bloki, Duplek - Zgornji Duplek, Duplek - Zgornji Duplek bloki, Gorišnica, Hajdina, Juršinci, Kidričevo, Kidričevo - Bloki, Majšperk, Markovci, Podlehnik, Sveti Andraž, Trnovska vas, Videm, Vitanje, Zavrč, Zreče, Žetale <!-- codespell:ignore -->

### Municipalities split into two collection areas

Gorišnica, Hajdina, Juršinci and Markovci are each served on two different collection days, and the provider publishes a separate schedule ("1. dan" / "2. dan") for each. The names are identical in the API, so these areas can only be told apart by their region ID:

| Municipality | Villages | Region ID |
|---|---|---|
| Gorišnica 1 | Cunkovci, Zagojiči, Gorišnica, Tibolci, Zamušani, Bresnica | 122 |
| Gorišnica 2 | Moškanjci, Gajevci, Mala vas, Formin, Placerovci, Muretinci | 123 | <!-- codespell:ignore vas -->
| Hajdina 1 | Slovenija vas, Hajdoše, Skorba, Spodnja Hajdina | 126 | <!-- codespell:ignore vas -->
| Hajdina 2 | Zgornja Hajdina, Gerečja vas, Draženci | 127 | <!-- codespell:ignore vas -->
| Juršinci 1 | Grlinci, Gradiščak, Zagorci, Sakušak, Bodkovci, Senčak pri Juršincih, Juršinci | 128 |
| Juršinci 2 | Hlapovci, Mostje, Kukava, Gabrnik, Rotman, Dragovič | 129 |
| Markovci 1 | Nova vas pri Markovcih, Bukovci, Stojnci | 125 | <!-- codespell:ignore vas -->
| Markovci 2 | Borovci, Prvenci, Strelci, Sobetinci, Markovci, Zabovci | 124 |

When configuring through the UI, pick the matching entry from the dropdown; it already contains the villages and the region ID. In YAML, pass the region ID (for example `region: 126`). Passing just the municipality name for one of these four raises an error listing the available IDs, so nothing is silently guessed for you.

The current split per municipality can always be checked against the official schedules on [cistomesto.si](https://cistomesto.si/urniki-odvoza-odpadkov/).

# GOAP Poznań

Support for schedules provided by [GOAP](https://www.goap.poznan.pl/) — Związek Międzygminny "Gospodarka Odpadami Aglomeracji Poznańskiej" (the Inter-municipal Union for Waste Management of the Poznań Agglomeration), Poland. This covers many municipalities in the Poznań agglomeration, e.g. Murowana Goślina, Czerwonak, Swarzędz and others.

The online calendar is hosted at [web.c-trace.de/zmgoappoznan-abfallkalender](https://web.c-trace.de/zmgoappoznan-abfallkalender/kalendarzodpadow) — use it to look up your exact city, street and house number values before configuring this source.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: goap_poznan_pl
      args:
        city: HUTA PUSTA
        street: HUTA PUSTA
        house_number: "1"
```

### Configuration Variables

**city** *(string) (required)*: City/village name exactly as used on the GOAP calendar (usually upper case), e.g. `MUROWANA GOŚLINA`.

**street** *(string) (required)*: Street name exactly as used on the GOAP calendar (usually upper case). For villages without named streets this is often the same as the city.

**house_number** *(string) (required)*: House number, including any letter/slash suffix exactly as shown on the GOAP calendar (e.g. `5` or `5/A`).

**location_type** *(string) (optional)*: Only needed if the address is ambiguous. One of: `Z` (inhabited), `N` (uninhabited), `M` (mixed), `R` (recreational).

**building_type** *(string) (optional)*: Only needed if the address is ambiguous. One of: `J` (single-family building), `W` (multi-family building).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: goap_poznan_pl
      args:
        city: "HUTA PUSTA"
        street: "HUTA PUSTA"
        house_number: "1"
        location_type: "Z"
        building_type: "J"
```

```yaml
waste_collection_schedule:
  sources:
    - name: goap_poznan_pl
      args:
        city: "MUROWANA GOŚLINA"
        street: "POZNAŃSKA"
        house_number: "17"
```

## How to get the source argument values

1. Open the [GOAP waste calendar](https://web.c-trace.de/zmgoappoznan-abfallkalender/kalendarzodpadow).
2. Enter your city (Miasto), street (Ulica) and house number (Nr domu), plus location/building type if requested, until the schedule ("Harmonogram") appears.
3. Use the exact same values (usually upper case) for `city`, `street` and `house_number` in your configuration.

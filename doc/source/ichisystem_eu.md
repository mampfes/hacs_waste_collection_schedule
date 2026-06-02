# Hemar (ichisystem.eu)

Support for waste collection schedules provided by the [Hemar harmonogram platform](https://harmonogram.ichisystem.eu/hemar/), Poland.

The Hemar platform is operated by Hemar / ichisystem.eu and is currently used by Pobiedziska and several neighbouring towns in Wielkopolska. The list of supported localities is fetched live from the portal — if your city is in the dropdown at <https://harmonogram.ichisystem.eu/hemar/>, this source will work for you.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ichisystem_eu
      args:
        city: CITY
        street: STREET
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**city**
*(string) (required)*

City / town name as listed on the Hemar portal. Matching is case-insensitive and tolerant of Polish diacritics.

**street**
*(string) (required)*

Street name as listed on the Hemar portal. Matching is case-insensitive and tolerant of Polish diacritics.

**house_number**
*(string) (required)*

House number as listed on the Hemar portal. Use exactly the value shown in the dropdown (for example `2`, `4 / 1`, or `2A/1`).

## How to find your `city`, `street`, and `house_number`

1. Open <https://harmonogram.ichisystem.eu/hemar/>.
2. Pick your locality from the **Miejscowość** dropdown.
3. Pick your street from the **Ulica** dropdown.
4. Pick your address from the **Nr posesji** dropdown.
5. Use those three values in your configuration.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ichisystem_eu
      args:
        city: Pobiedziska
        street: Boczna
        house_number: "2"
```

## Bin types returned

The waste-type label returned by this source is the exact column header from the provider's schedule table (in Polish). Icons are mapped automatically:

| Provider description (Polish)        | Icon              |
|--------------------------------------|-------------------|
| Zmieszane odpady komunalne           | `mdi:trash-can`   |
| Papier                               | `mdi:newspaper`   |
| Metale i tworzywa sztuczne           | `mdi:recycle`     |
| Szkło                                | `mdi:bottle-wine` |
| Bioodpady                            | `mdi:leaf`        |
| Bioodpady - Drzewka świąteczne       | `mdi:pine-tree`   |
| Odpady wystawkowe                    | `mdi:sofa`        |

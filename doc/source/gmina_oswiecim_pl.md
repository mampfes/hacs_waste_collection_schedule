# Gmina Oświęcim

Support for schedules provided by [Gmina Oświęcim](https://zuk.oswiecim.pl).

Source for ZUK Oświęcim waste collection in Gmina Oświęcim, Poland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gmina_oswiecim_pl
      args:
        city: CITY
        street: STREET
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (required)*

**house_number**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: gmina_oswiecim_pl
      args:
        city: Brzezinka
        street: Niwy
```

## How to get the source arguments

On https://zuk.oswiecim.pl/harmonogramy open the Gmina Oświęcim schedule for detached houses (zabudowa jednorodzinna). Enter your village (sołectwo, e.g. 'Brzezinka') and your street as printed there (e.g. 'Niwy'). Ofiar Faszyzmu is split by house number: 14-18 is a separate mixed-waste round, so enter the house number too. Bulky waste and kitchen bio-waste are collected on the printed days only after you book them with ZUK. Multi-family buildings and the town of Oświęcim are not covered.

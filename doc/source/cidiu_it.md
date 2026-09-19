# CIDIU S.p.A.

Support for schedules provided by [CIDIU S.p.A.](https://www.cidiu.it/), in the north-west Turin province in Italy.

CIDIU no longer runs its own calendar page. Its schedules are published through the [Junker app](https://junker.app), which has one zone per street (or per range of street numbers). This source looks up the zone that covers your street and number and returns that zone's calendar.

## How to get the configuration arguments

- Browse to the [Junker calendar](https://differenziata.junkerapp.it/collegno/calendario) for your town (replace `collegno` with your town's name in the address).
- Find your street in the list. Zones for long streets are split by number range, for example `CORSO SUSA pari da 2 a 314 dispari da 17 a 315`.
- Use the town, street name and street number in the configuration.

If your street is spelled differently by Junker (for example `Viale Antonio Gramsci` where you would write `Viale Gramsci`), the source tries to match on the words you give. If it cannot find exactly one zone it lists the matching zone names in the error message.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: cidiu_it
      args:
        city: Collegno
        street: via Condove
        street_number: '107'

```

### Configuration Variables

**city**  
*(string (required))*

Your town. All towns served by CIDIU are listed on the [available services](https://cidiu.it/cidiu/servizi-nei-comuni/) page.

**street**  
*(string) (required)*

Street name without the number, as it appears in the Junker calendar for your town.

**street_number**  
*(string) (required)*

Street number. Only the leading digits are used to pick the zone (`3/A` is treated as `3`).

## Returned Collections

This source returns the collections published in the Junker calendar for your zone. Collection types are the ones Junker uses (for example *General waste collection*, *Organic waste*, *Paper*, *Plastic* and *Glass/Cans*).

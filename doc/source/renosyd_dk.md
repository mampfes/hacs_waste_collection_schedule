# Renosyd i/s

Support for schedules provided by [Renosyd i/s](https://renosyd.dk/), serving Odder and Skanderborg kommuner, Denmark.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: renosyd_dk
      args:
        house_number: See description

```

### Configuration Variables

**house_number**
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: renosyd_dk
      args:
        house_number: "023000"

```

## How to get the house number / husnummer

Go to the [Mit renosyd](https://mit.renosyd.dk/toemmekalender) page, enter your address and click "Gem".

Your house number is saved in Local Storage. To get this, you can:
1) Open Developer Console
   - Chrome / Microsoft Edge: `CTRL + SHIFT + J` or `Cmd + Option + J`
   - Firefox: `CTRL + SHIFT + K` or `Cmd + Option + K`
   - Safari: `CMD + OPTION + C`
2) Paste the following and press `enter`, which will output the number you need: `JSON.parse(localStorage.getItem('bookmarkedCollectionSites'))[0].standpladsNummer`

### Filtering Example

hiding `Storskrald`

```yaml
waste_collection_schedule:
    sources:
    - name: renosyd_dk
      args:
        house_number: 123001
      customize:
        - type: Storskrald
          show: false

```

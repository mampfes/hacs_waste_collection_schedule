# Abfall Kreis Tuebingen

Support for Abfall Kreis Tuebingen.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_kreis_tuebingen
      args:
        ort: ORT
        dropzone: DROPZONE
        ics_with_drop: ICS_WITH_DROP
```

### Configuration Variables

**ort**<br>
*(integer) (required)*

**dropzone**<br>
*(integer) (required)*

**ics_with_drop**<br>
*(boolean) (optional, default: ```False```)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_kreis_tuebingen
      args:
        ort: 3
        dropzone: 525
```

## How to get the source arguments

The simplest way get the source arguments is to us a (desktop) browser with developer tools, e.g. Google Chrome:

1. Open [https://www.abfall-kreis-tuebingen.de/services/online-abfuhrtermine/](https://www.abfall-kreis-tuebingen.de/services/online-abfuhrtermine/).
2. Enter your data, but don't click on "ICS Download" so far!
3. Open the Developer Tools (Ctrl + Shift + I) and open the `Network` tab.
4. Now click the "ICS Download" button.
5. You should see (amongst other's) one entry labeled `admin-ajax.php` in the network recording.
6. Select `admin-ajax.php` on the left hand side and scroll down to `Form Data` on the right hand side.
7. Here you can find the values for `ort` and `dropzone`.

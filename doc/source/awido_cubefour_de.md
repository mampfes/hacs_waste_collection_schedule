# Cubefour AWIDO-based services

Cubefour AWIDO is a platform for waste schedules, which has several German cities and districts as customers. The homepage of the company is https://www.awido-online.de/.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: awido_cubefour_de
      args:
        customer: customer
        city: city
        street: street
        housenumber: 2
        fraktionen: 2,3,4
```

### Configuration Variables

**customer**<br>
*(string) (required)*

**city**<br>
*(string) (required)*

**street**<br>
*(integer) (depend on customer)*

**housenumber**<br>
*(integer) (depend on customer)*

**fraktionen**<br>
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: awido_cubefour_de
      args:
        customer: rmk
        city: Waiblingen
        street: Benzstr.
        housenumber: 14
        fraktionen: 2,3
```

## How to get the source arguments

### customer

List of customers (2021-07-09):
- `rmk`: AWG des Rems-Murr-Kreises mbH
- `lra-schweinfurt`: Landkreis Schweinfurt
- `gotha`: Landkreis Gotha
- `zaso`: Zweckverband Abfallwirtschaft Saale-Orla
- `unterhaching`: Gemeinde Unterhaching
- `kaufbeuren`: Stadt Kaufbeuren
- `bgl`: Landkreis Berchtesgadener Land
- `pullach`: Pullach im Isartal
- `ffb`: Landkreis Fürstenfeldbruck
- `unterschleissheim`: Stadt Unterschleißheim
- `kreis-tir`: Landkreis Tirschenreuth
- `rosenheim`: Landkreis Rosenheim
- `tuebingen`: Landkreis Tübingen
- `kronach`: Landkreis Kronach
- `erding`: Landkreis Erding
- `zv-muc-so`: Zweckverband München-Südost
- `coburg`: Landkreis Coburg
- `ansbach`: Landkreis Ansbach
- `awb-duerkheim`: AWB Landkreis Bad Dürkheim
- `aic-fdb`: Landratsamt Aichach-Friedberg
- `wgv`: WGV Recycling GmbH
- `neustadt`: Neustadt a.d. Waldnaab
- `kelheim`: Landkreis Kelheim
- `kaw-guenzburg`: Landkreis Günzburg
- `memmingen`: Stadt Memmingen
- `eww-suew`: Landkreis Südliche Weinstraße
- `lra-dah`: Landratsamt Dachau
- `landkreisbetriebe`: Landkreisbetriebe Neuburg-Schrobenhausen
- `awb-ak`: Abfallwirtschaftsbetrieb Landkreis Altenkirchen
- `awld`: Abfallwirtschaft des Lahn-Dill-Kreises
- `azv-hef-rof`: Abfallwirtschafts-Zweckverband des Landkreises Hersfeld-Rotenburg
- `awv-nordschwaben`: Abfall-Wirtschafts-Verband Nordschwaben

### fraktionen

Go to your calender at `https://awido.cubefour.de/Customer/<customer>/v2/Calendar2.aspx`, select a city, street and housenumber and then select the types of waste you want to have. Afterwards enter this in the address bar and press Enter: `javascript:alert(document.querySelector('#Content_SelectedFractions').value)`

Copy the value which is shown in the alert dialog and paste it as the argument fraktionen in the config.

### city, street etc.

Go to your calender at `https://awido.cubefour.de/Customer/<customer>/v2/Calendar2.aspx`. The first entry is the `city` (except for single-city customers, then the parameter `city` is the city), then the `street` and depending on the customer then the `housenumber`.

# AWIDO based services

Cubefour AWIDO is a platform for waste schedules, which has several German cities and districts as customers. The homepage of the company is https://www.awido-online.de/.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: awido_de
      args:
        customer: customer
        city: city
        street: street
        housenumber: 2
```

### Configuration Variables

**customer**<br>
*(string) (required)*

**city**<br>
*(string) (required)*

**street**<br>
*(integer) (optional, depends on customer)*

**housenumber**<br>
*(integer) (optional, depends on customer)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: awido_de
      args:
        customer: rmk
        city: Waiblingen
        street: Benzstr.
        housenumber: 14
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
- `zv-muc-so`: Zweckverband München-Südost

### city, street, house number

- Go to your calendar at `https://awido.cubefour.de/Customer/<customer>/v2/Calendar2.aspx`. Replace `<customer>` with the one of the keys listed above.
- Enter your city name from the first page into the `city` field.
- If you have to enter a street or district, enter the name into the `street` field.
- If you have to enter a house number, enter the house number into the `housenumber` field.

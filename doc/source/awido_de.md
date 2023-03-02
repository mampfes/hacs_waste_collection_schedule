# AWIDO based services

Cubefour AWIDO is a platform for waste schedules, which has several German cities and districts as customers. The homepage of the company is [https://www.awido-online.de/](https://www.awido-online.de/).

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

**customer**  
*(string) (required)*

**city**  
*(string) (required)*

**street**  
*(integer) (optional, depends on customer)*

**housenumber**  
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

<!--Begin of service section-->
- `aic-fdb`: Landratsamt Aichach-Friedberg
- `ansbach`: Landkreis Ansbach
- `awb-ak`: Abfallwirtschaftsbetrieb Landkreis Altenkirchen
- `awb-duerkheim`: AWB Landkreis Bad Dürkheim
- `awld`: Abfallwirtschaft Lahn-Dill-Kreises
- `awv-isar-inn`: Abfallwirtschaft Isar-Inn
- `awv-nordschwaben`: Abfall-Wirtschafts-Verband Nordschwaben
- `azv-hef-rof`: Abfallwirtschafts-Zweckverband des Landkreises Hersfeld-Rotenburg
- `bgl`: Landkreis Berchtesgadener Land
- `coburg`: Landkreis Coburg
- `erding`: Landkreis Erding
- `eww-suew`: Landkreis Südliche Weinstraße
- `ffb`: AWB Landkreis Fürstenfeldbruck
- `fulda`: Abfallwirtschaft Fulda
- `gotha`: Landkreis Gotha
- `kaufbeuren`: Stadt Kaufbeuren
- `kaw-guenzburg`: Landkreis Günzburg
- `kelheim`: Landkreis Kelheim
- `kreis-tir`: Landkreis Tirschenreuth
- `kronach`: Landkreis Kronach
- `landkreisbetriebe`: Landkreisbetriebe Neuburg-Schrobenhausen
- `lra-dah`: Landratsamt Dachau
- `lra-schweinfurt`: Landkreis Schweinfurt
- `memmingen`: Stadt Memmingen
- `neustadt`: Neustadt a.d. Waldnaab
- `pullach`: Pullach im Isartal
- `regensburg`: Stadt Regensburg
- `rmk`: Abfallwirtschaft Rems-Murr
- `rosenheim`: Landkreis Rosenheim
- `tuebingen`: Landkreis Tübingen
- `unterhaching`: Gemeinde Unterhaching
- `unterschleissheim`: Stadt Unterschleißheim
- `wgv`: WGV Recycling GmbH
- `zaso`: Zweckverband Abfallwirtschaft Saale-Orla
- `zv-muc-so`: Zweckverband München-Südost
<!--End of service section-->

### city, street, house number

- Go to your calendar at `https://awido.cubefour.de/Customer/<customer>/v2/Calendar2.aspx`. Replace `<customer>` with the one of the keys listed above.
- Enter your city name from the first page into the `city` field.
- If you have to enter a street or district, enter the name into the `street` field.
- If you have to enter a house number, enter the house number into the `housenumber` field.

# C-Trace.de

Support for schedules provided by [c-trace.de](https://www.c-trace.de) which is servicing multiple municipalities.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: c_trace_de
      args:
        service: SERVICE
        ort: ORT
        gemeinde: GEMEINDE
        ortsteil: ORTSTEIL
        strasse: STRASSE
        hausnummer: HAUSNUMMER
        abfall: ABFALLARTEN
```

### Configuration Variables

**service**
*(string) (required)*
Name of the service which is specific to your municipality. See the table below to get the right value for your location.

**ort**
*(string) (optional)*
Needed for most municipalities but no all

**gemeinde**
*(string) (optional)*
Needed for some municipalities but not all (can be left empty if same as `ort` or unneeded)

**ortsteil**
*(string) (optional)*
Needed only for some municipalities but not all (can be left empty if unneeded)

**strasse**
*(string) (required)*

**hausnummer**
*(string) (required)*

**abfall**
*(string) (optional)*
Pipe-separated waste type IDs to filter which types are returned (e.g. `0|1|2|5`). If empty, all waste types are fetched. This is important for providers like Main-Tauber-Kreis where multiple Restabfall frequencies exist (weekly, 14-day, 4-weekly) but all appear as "Restabfall" in the calendar. Use the `abfall` parameter to select only your frequency. Visit your provider's calendar page to see the checkbox list of waste types — the IDs correspond to their order (0 for the first, 1 for the second, etc.).

## Example

```yaml
waste_collection_schedule:
  sources:
  - name: c_trace_de
    args:
      ort: Riedstadt
      ortsteil: Crumstadt
      strasse: Am Lohrrain
      hausnummer: 3
      service: grossgeraulandkreis-abfallkalender
```

```yaml
waste_collection_schedule:
  sources:
    - name: c_trace_de
      args:
        service: bremenabfallkalender
        ort: Bremen
        strasse: Abbentorstraße
        hausnummer: 5
```

```yaml
waste_collection_schedule:
  sources:
  - name: c_trace_de
    args:
      strasse: Am Kindergarten
      hausnummer: 1
      service: landau
```

```yaml
waste_collection_schedule:
  sources:
  - name: c_trace_de
    args:
      strasse: Am Reidigermeer
      hausnummer: 2d/e
      service: aurich-abfallkalender
      gemeinde: Aurich
      ort: Kirchdorf
```

### Main-Tauber-Kreis with 4-weekly Restabfall

```yaml
waste_collection_schedule:
  sources:
  - name: c_trace_de
    args:
      ort: Tauberbischofsheim
      strasse: Hauptstraße
      hausnummer: 1
      service: maintauberkreis-abfallkalender
      abfall: "0|1|2|5"
```

The waste type IDs for Main-Tauber-Kreis are: 0=Bioabfall, 1=Gelbe Tonne, 2=Papierabfall, 3=Restabfall wöchentlich, 4=Restabfall 14-täglich, 5=Restabfall 4-wöchentlich. Use only the ID for your Restabfall frequency.

## How to get the source arguments

This source requires the name of a `service` which is specific to your municipality. Use the following map to get the right value for your district.

<!--Begin of service section-->
|Municipality|service|
|-|-|
| Abfallwirtschaft Rheingau-Taunus-Kreis | `rheingauleerungen` |
| Abfallwirtschaftsbetrieb Landkreis Augsburg | `augsburglandkreis` |
| Abfallwirtschaftsbetrieb Landkreis Aurich | `aurich-abfallkalender` |
| Abfallwirtschaftsverband Kreis Groß-Gerau | `grossgeraulandkreis-abfallkalender` |
| Bau & Service Oberursel | `oberursel` |
| Bremer Stadtreinigung | `bremenabfallkalender` |
| Entsorgungs- und Wirtschaftsbetrieb Landau in der Pfalz | `landau` |
| Kreisstadt Dietzenbach | `dietzenbach` |
| Kreisstadt St. Wendel | `stwendel` |
| Landkreis Roth | `roth` |
| Landratsamt Main-Tauber-Kreis | `maintauberkreis-abfallkalender` |
| Stadt Arnsberg | `arnsberg-abfallkalender` |
| Stadt Bayreuth | `bayreuthstadt-abfallkalender` |
| WZV Kreis Segeberg | `segebergwzv-abfallkalender` |
<!--End of service section-->

## Tip

If your waste-service has an online-tool where you can get an ical or CSV-File, you can extract the needed `service` from the URL of the files.
![image](https://user-images.githubusercontent.com/2480235/210091450-663907b0-6a9c-45b4-b0ae-00110896bb08.png)


Link for above image: https://web.c-trace.de/segebergwzv-abfallkalender/(S(ebi2zcbvfeqp0za3ofnepvct))/abfallkalender/cal/2023?Ort=Bad%20Segeberg&Strasse=Am%20Wasserwerk&Hausnr=2&abfall=0|1|2|3|4|5|6|7|

From this Link you can extract the following parameters:

`web|app`.c-trace.de/`(web.)service`/some-id/abfallkalender/`cal|downloadcal` `/year|`?Ort=`ort`&Ortsteil=`ortsteil`&Strasse=`strasse`&Hausnr=`hausnummer`&abfall='abfallarten'...

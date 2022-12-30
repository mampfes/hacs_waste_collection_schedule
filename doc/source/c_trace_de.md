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
        strasse: STRASSE
        hausnummer: HAUSNUMMER
```

### Configuration Variables

**service**  
*(string) (required)*  
Name of the service which is specific to your municipality. See the table below to get the right value for your location.

**ort**  
*(string) (required)*

**strasse**  
*(string) (required)*

**hausnummer**  
*(string) (required)*

## Example

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

## How to get the source arguments

This source requires the name of a `service` which is specific to your municipality. Use the following map to get the right value for your district.

|Municipality|service|
|-|-|
|Bremen|`bremenabfallkalender`|
|AWB Landkreis Augsburg|`augsburglandkreis`|
|WZV Kreis Segeberg|`segebergwzv-abfallkalender`|

## Tip

If your waste-service has an online-tool where you can get an ical or CSV-File, you can extract the needed `service` from the URL of the files.
![image](https://user-images.githubusercontent.com/2480235/210090615-29521bf0-eeaf-405d-8d02-56a505401f07.png)

Link for above image: https://web.c-trace.de/segebergwzv-abfallkalender/(S(yoxdsu4g1uzrk3vt5gkztnae))/abfallkalender/cal/2023?Ort=Bad%20Segeberg&Strasse=Am%20Bienenhof&Hausnr=1%2B1a&abfall=0|1|2|3|4|5|6|7|

From this Link you can extract the following parameters:

web.c-trace.de/`service`/some-id/abfallkalender/cal/year?Ort=`ort`&Strasse=`strasse`&Hausnr=`hausnummer`...

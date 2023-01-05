# Umweltprofis.at

Support for schedules provided by [Umweltprofis.at](https://www.umweltprofis.at).

## Configuration via configuration.yaml

You need to generate your personal XML link before you can start using this source. Go to [https://data.umweltprofis.at/opendata/AppointmentService/index.aspx](https://data.umweltprofis.at/opendata/AppointmentService/index.aspx) and fill out the form. At the end at step 6 you get a link to a XML file. Copy this link and paste it to configuration.yaml as seen below.

```yaml
waste_collection_schedule:
  sources:
    - name: data_umweltprofis_at
      args:
        xmlurl: URL
```

### Configuration Variables

**xmlurl**  
*(URL) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: data_umweltprofis_at
      args:
        xmlurl: https://data.umweltprofis.at/opendata/AppointmentService/AppointmentService.asmx/GetTermineForLocationSecured?Key=TEMPKeyabvvMKVCic0cMcmsTEMPKey&StreetNr=124972&HouseNr=Alle&intervall=Alle
```

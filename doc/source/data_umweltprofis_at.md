# Umweltprofis

Support for schedules provided by [Umweltprofis](https://www.umweltprofis.at).

Source for Umweltprofis

## Configuration via configuration.yaml

### Using url

```yaml
waste_collection_schedule:
  sources:
    - name: data_umweltprofis_at
      args:
        url: URL
```

### Using xmlurl

```yaml
waste_collection_schedule:
  sources:
    - name: data_umweltprofis_at
      args:
        xmlurl: XMLURL
```

### Configuration Variables

**url**  
*(string) (alternative)*

**xmlurl**  
*(string) (alternative)*

Provide one of: `url` or `xmlurl`.

## Example

### Using url

```yaml
waste_collection_schedule:
  sources:
    - name: data_umweltprofis_at
      args:
        url: https://data.umweltprofis.at/OpenData/AppointmentService/AppointmentService.asmx/GetIcalWastePickupCalendar?key=KXX_K0bIXDdk0NrTkk3xWqLM9-bsNgIVBE6FMXDObTqxmp9S39nIqwhf9LTIAX9shrlpfCYU7TG_8pS9NjkAJnM_ruQ1SYm3V9YXVRfLRws1
```

### Using xmlurl

```yaml
waste_collection_schedule:
  sources:
    - name: data_umweltprofis_at
      args:
        xmlurl: https://data.umweltprofis.at/opendata/AppointmentService/AppointmentService.asmx/GetTermineForLocationSecured?Key=TEMPKeyabvvMKVCic0cMcmsTEMPKey&StreetNr=118213&HouseNr=Alle&intervall=Alle
```

## How to get the source arguments

You need to generate your personal XML link before you can start using this source. Go to https://data.umweltprofis.at/opendata/AppointmentService/index.aspx and fill out the form. At the end, step 6 gives you a link to an XML file. Copy this link and use it as the XML URL.

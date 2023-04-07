# Hausmüll.info

Support for schedules provided by [Hausmuell.info](https://hausmuell.info), serving multiple areas in Germany.

## Known supported providers

|Provider|URL|Subdomain (needed for configuration)|
|-|-|-|
|Eigenbetrieb Kommunalwirtschaftliche Dienstleistungen Suhl|[ebkds.de](https://www.ebkds.de)|ebkds|
|Stadtwerke Erfurt SWE|[stadtwerke-erfurt.de](https://www.stadtwerke-erfurt.de)|erfurt|
|Kreiswerke Schmalkalden-Meiningen GmbH|[kwsm.de](https://www.kwsm.de)|schmalkalden-meiningen|
|Eichsfeldwerke GmbH|[eichsfeldwerke.de](https://www.eichsfeldwerke.de)|ew|
|Abfallwirtschaftszweckverband Wartburgkreis (AZV)|[azv-wak-ea.de](https://www.azv-wak-ea.de)|azv|
|Landkreis Börde AöR (KsB)|[ks-boerde.de](https://www.ks-boerde.de)|boerde|
|Chemnitz (ASR)|[asr-chemnitz.de](https://www.asr-chemnitz.de)|asc|
|ASG Wesel|[asg-wesel.de](https://www.asg-wesel.de)|wesel|

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: hausmuell_info
      args:
        ort: ORT
        strasse: STRAßE
        Hausnummer: HNR
        subdomain: SUBDOMAIN
        
```

### Configuration Variables

**subdomain**  
*(String) (required)*  
The subdomain, that the provider uses for communication with ***subdomain***.hausmuell.info.

**ort**  
*(String) (optional)*

**ortsteil**  
*(String) (optional)*

**strasse**  
*(String) (optional)*

**Hausnummer**  
*(String | Integer) (optional)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: hausmuell_info
      args:
        subdomain: ebkds
        ort: Dietzhausen
        strasse: Am Rain
        Hausnummer: "10"      
        
```

## How to get the source argument

You can find your providers hausmuell.info subdomain in the Table above. If your provider uses hausmuell.info but is not in the list above you can find the subdomain by opening the inspection tools in your browser and use the network tab to search any traffic to ***subdomain***.hausmuell.info

Find the other parameter of your address by going to your providers' website to the `abfallkalender` section. Fill in your address and use this as your configuration variables. Note not all providers need all arguments, so you probably do not need all of them.

# Hausmüll.info

Support for schedules provided by [Hausmuell.info](https://hausmuell.info), serving multiple areas in Germany.

## Known supported providers

|Provider|URL|domain (needed for configuration)|
|-|-|-|
|Eigenbetrieb Kommunalwirtschaftliche Dienstleistungen Suhl|[ebkds.de](https://www.ebkds.de)|ebkds.hausmuell.info|
|Stadtwerke Erfurt SWE|[stadtwerke-erfurt.de](https://www.stadtwerke-erfurt.de)|abfallkalender.stadtwerke-erfurt.de|
|Kreiswerke Schmalkalden-Meiningen GmbH|[kwsm.de](https://www.kwsm.de)|schmalkalden-meiningen.hausmuell.info|
|Eichsfeldwerke GmbH|[eichsfeldwerke.de](https://www.eichsfeldwerke.de)|ew.hausmuell.info|
|Abfallwirtschaftszweckverband Wartburgkreis (AZV)|[azv-wak-ea.de](https://www.azv-wak-ea.de)|azv.hausmuell.info|
|Landkreis Börde AöR (KsB)|[ks-boerde.de](https://www.ks-boerde.de)|boerde.hausmuell.info|
|Chemnitz (ASR)|[asr-chemnitz.de](https://www.asr-chemnitz.de)|asc.hausmuell.info|
|ASG Wesel|[asg-wesel.de](https://www.asg-wesel.de)|wesel.hausmuell.info|

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: hausmuell_info
      args:
        ort: ORT
        strasse: STRAßE
        Hausnummer: HNR
        domain: domain
        
```

### Configuration Variables

**domain**  
*(String) (required)*  
The domain, that the provider uses for communication with hausmuell.info.

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
        domain: ebkds.hausmuell.info
        ort: Dietzhausen
        strasse: Am Rain
        Hausnummer: "10"      
        
```

## How to get the source argument

You can find your providers hausmuell.info domain in the Table above. If your provider uses hausmuell.info but is not in the list above you can find the domain by opening the inspection tools in your browser and use the network tab to search any traffic to hausmuell.info

Find the other parameter of your address by going to your providers' website to the `abfallkalender` section. Fill in your address and use this as your configuration variables. Note not all providers need all arguments, so you probably do not need all of them.

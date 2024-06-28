# Affaldonline

Support for schedules from Affaldonline, which serves several Danish municipalities.

The layout of the response page may differ. There seems to be a default, but I've stumpled upon at least a few uniques.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
        - name: affaldonline_dk
          args:
              municipality: "favrskov"
              values: "Nørregade|1||||8382|Hinnerup|6443|108156|0"
```

### Configuration Variables

**municipality**  
_(String) (required)_

An affaldonline defined string for the municipality. I.e. "aeroe" for "Ærø". 

A duckduckgo search revealed many of them:

- [DuckDuckGo](https://duckduckgo.com/?t=h_&q=site%3Aaffaldonline.dk%2Fkalender%2F&ia=web)

**values**  
_(String) (required)_

A string that includes the street name, house number, postal code, city name, and some numbers that seems to be internal affaldonline references. 

## How to find the "values" string to use

Go to the Affaldonline site for your municipality: 

- [Ærø](https://www.affaldonline.dk/kalender/aeroe/)
- [Assens](https://www.affaldonline.dk/kalender/assens/)
- [Favrskov](https://www.affaldonline.dk/kalender/favrskov/)
- [Fanø](https://www.affaldonline.dk/kalender/fanoe/)
- [Fredericia](https://www.affaldonline.dk/kalender/fredericia/)
- [Langeland](https://www.affaldonline.dk/kalender/langeland/)
- [Middelfart](https://www.affaldonline.dk/kalender/middelfart/)
- [Nyborg](https://www.affaldonline.dk/kalender/nyborg/)
- [Rebild](https://www.affaldonline.dk/kalender/rebild/)
- [Silkeborg](https://www.affaldonline.dk/kalender/silkeborg/)
- [Sorø](https://www.affaldonline.dk/kalender/soroe/)
- [Vejle](https://www.affaldonline.dk/kalender/vejle/)

Open the developer console in your browser.

Enter your address and select the house number in the dropdown menu.

In the Network tab in the browser console, select the latest URL ending in **showInfo.php** and look under Payload, where you should find the **values** variable ready for copy/paste.

Depending on your browser, it should also be possible to right-click the house number field, and select "Inspect" - this should give you the html for the field, and here you can select the value from your house number in the list.

### Customizing Waste Types

Customizing waste types is a feature of the Waste Collection Schedule component and is very useful here, since the waste types in affaldonline are often long and not very consistent.

```yaml
waste_collection_schedule:
    sources:
        - name: affaldonline_dk
          args:
              municipality: "favrskov"
              values: "Nørregade|1||||8382|Hinnerup|6443|108156|0"
          customize:
              - type: "Plast/mad- og drikkekartoner og glas/metal"
                alias: "Plast/glas/metal"
```

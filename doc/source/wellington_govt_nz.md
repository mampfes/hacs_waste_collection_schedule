# Wellington City Council

Support for schedules provided by [Wellington City Council](https://wellington.govt.nz/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: wellington_govt_nz
      args:
        streetName: Street Name, Suburb # see 'How to get the source argument below'
        streetId: streetID Number 
```

### Configuration Variables

**streetName**  
*(string)*

**streetId**  
*(string)*

*One of the above is required*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: wellington_govt_nz
      args:
        streetName: Chelsea Street
```

```yaml
waste_collection_schedule:
  sources:
    - name: wellington_govt_nz
      args:
        streetId: 6515
```

## How to get the source argument

The source argument is the either the street name or street id number from Wellington City Council site:

- Open your *When to put out your rubbish and recycling* page, and enter your address in the search box [on the Wellington City Council collection day finder](https://wellington.govt.nz/rubbish-recycling-and-waste/when-to-put-out-your-rubbish-and-recycling)
- The "streetName" variable uses the same code that the search box uses to find the streetId from your street name, suburb. But like the search box you do not need to enter the full name if your text matches only one result. For example "Miramar" would get you two results for Miramar Ave, Miramar and Miramar North Road, Miramar and the script would error as it can only deal with one street per call, so you would need to write "Miramar Ave" or "Miramar Avenue" etc to get the right result.
- If you are having issues with the script finding your street, or you can't get it to narrow the result without selection options on the Wellington Council site, you can use the streetId parameter directly.
- Once you have found your street on the website, look at the blue button which is meant to show you the next weeks collection info, if you hover over the button, right click and copy link, you should get back a URL e.g. https://wellington.govt.nz/rubbish-recycling-and-waste/when-to-put-out-your-rubbish-and-recycling/components/collection-search-results?streetId=8187&addWeeks=1
- Look for the streetId parameter in the URL in the example link above, it is streetId=`8187`

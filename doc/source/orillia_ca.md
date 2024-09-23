# Orillia, Ontario

Support for schedules provided by [Orillia, Ontario](https://www.orillia.ca/), serving Orilla City, Canada.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: orillia_ca
      args:
        email: EMAIL
        password: PASSWORD
```

### Configuration Variables

**email**  
*(String) (required)*

**password**  
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: orillia_ca
      args:
        email: !secret orilla_email
        password: !secret orilla_password
        
```

## How to get the source argument

Make an account on the [OrilliaNow](https://www.orillia.ca/https://orillianow.orillia.ca/login) website and login. Add your address to your account. You can now use the email and password you used to login to the website as the source arguments.

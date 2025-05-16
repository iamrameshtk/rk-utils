# SSL Certificate Validation Guide

This guide provides tools and code snippets to troubleshoot SSL certificate issues, particularly when working with APIs like Data Fusion that require secure connections.

## Table of Contents
- [Using curl to inspect SSL certificates](#using-curl-to-inspect-ssl-certificates)
- [Python scripts for SSL certificate inspection](#python-scripts-for-ssl-certificate-inspection)
- [Testing APIs with different SSL verification settings](#testing-apis-with-different-ssl-verification-settings)
- [Common SSL issues and solutions](#common-ssl-issues-and-solutions)
- [Using the certifi module in Python](#using-the-certifi-module-in-python)

## Using curl to inspect SSL certificates

```bash
# Basic SSL certificate information
curl -v https://your-datafusion-endpoint.com 2>&1 | grep -i "SSL\|TLS\|certificate"

# More detailed certificate information
curl --insecure -v https://your-datafusion-endpoint.com 2>&1 | grep -i "SSL\|TLS\|certificate"

# Save the certificate to a file
echo | openssl s_client -servername your-datafusion-endpoint.com -connect your-datafusion-endpoint.com:443 | sed -ne '/-BEGIN CERTIFICATE-/,/-END CERTIFICATE-/p' > certificate.pem

# View certificate details
openssl x509 -in certificate.pem -text -noout
```

## Python scripts for SSL certificate inspection

### Basic SSL Certificate Inspection

```python
import ssl
import socket
import datetime
import pprint

def get_certificate_details(hostname, port=443):
    context = ssl.create_default_context()
    # Don't check hostname or certificate for this check
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    
    with socket.create_connection((hostname, port)) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            cert = ssock.getpeercert(binary_form=False)
            return cert

def print_cert_info(cert):
    # Format expiration dates
    not_before = datetime.datetime.strptime(cert['notBefore'], '%b %d %H:%M:%S %Y %Z')
    not_after = datetime.datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
    
    print(f"Subject: {dict(x[0] for x in cert['subject'])}")
    print(f"Issuer: {dict(x[0] for x in cert['issuer'])}")
    print(f"Valid from: {not_before}")
    print(f"Valid until: {not_after}")
    print(f"Serial Number: {cert['serialNumber']}")
    
    # Check if the certificate is expired
    now = datetime.datetime.now()
    if now > not_after:
        print("CERTIFICATE IS EXPIRED!")
    
    # Print SAN (Subject Alternative Names)
    for ext in cert.get('subjectAltName', []):
        print(f"SAN: {ext}")

if __name__ == "__main__":
    hostname = "your-datafusion-endpoint.com"  # Replace with your actual endpoint
    try:
        cert = get_certificate_details(hostname)
        print_cert_info(cert)
    except Exception as e:
        print(f"Error: {e}")
```

## Testing APIs with different SSL verification settings

```python
import requests
import urllib3
import json

# Warning: Only disable warnings in debugging scenarios
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_api_with_ssl_options(url, headers=None, data=None):
    """Test the API with different SSL verification options"""
    
    if headers is None:
        headers = {'Content-Type': 'application/json'}
    
    print("\n1. With SSL verification (default)")
    try:
        response = requests.put(url, headers=headers, data=json.dumps(data) if data else None)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:100]}...")
    except requests.exceptions.SSLError as e:
        print(f"SSL Error: {e}")
    
    print("\n2. Without SSL verification (INSECURE - only for debugging)")
    try:
        response = requests.put(url, headers=headers, data=json.dumps(data) if data else None, verify=False)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:100]}...")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n3. With a custom CA bundle (if you have one)")
    try:
        # Replace with path to your CA bundle
        response = requests.put(url, headers=headers, data=json.dumps(data) if data else None, 
                             verify='/path/to/your/ca-bundle.crt')
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:100]}...")
    except Exception as e:
        print(f"Error: {e}")

# Example usage
url = "https://your-datafusion-endpoint.com/v3/namespaces/default/profiles/dataproc"
headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_TOKEN_HERE'  # Replace with your auth token
}
data = {
    "name": "dataproc",
    "description": "Dataproc profile",
    # Add other required fields for your profile
}

test_api_with_ssl_options(url, headers, data)
```

## Common SSL issues and solutions

1. **Self-signed certificate**: Add your certificate to the trusted CA store or use `verify=False` (for testing only)
2. **Certificate chain issues**: Ensure intermediate certificates are properly installed on the server
3. **Certificate hostname mismatch**: Ensure the hostname you're connecting to matches what's in the certificate
4. **Expired certificate**: Renew the certificate
5. **Clock synchronization**: Make sure your system clock is accurate

## Using the certifi module in Python

The `certifi` module in Python is a valuable tool for SSL certificate verification. It provides a curated collection of Root Certificates for validating the trustworthiness of SSL certificates while verifying the identity of TLS hosts.

### 1. Basic Installation

```bash
pip install certifi
```

### 2. Getting the path to the certificate bundle

```python
import certifi

# Get the path to the certifi CA bundle
ca_bundle_path = certifi.where()
print(f"Certifi CA bundle path: {ca_bundle_path}")
```

### 3. Using certifi with the requests library

```python
import requests
import certifi

url = "https://your-datafusion-endpoint.com"

# Explicitly use the certifi CA bundle
response = requests.get(url, verify=certifi.where())
print(f"Status code: {response.status_code}")
```

### 4. Using certifi with urllib3 directly

```python
import urllib3
import certifi

http = urllib3.PoolManager(
    cert_reqs='CERT_REQUIRED',
    ca_certs=certifi.where()
)

response = http.request('GET', 'https://your-datafusion-endpoint.com')
print(f"Status code: {response.status}")
```

### 5. Using certifi to inspect a certificate

```python
import ssl
import socket
import certifi
import datetime
import pprint

def get_certificate_details(hostname, port=443):
    # Create SSL context using certifi's trusted CA bundle
    context = ssl.create_default_context(cafile=certifi.where())
    
    with socket.create_connection((hostname, port)) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            cert = ssock.getpeercert(binary_form=False)
            return cert

def print_cert_info(cert):
    # Format expiration dates
    not_before = datetime.datetime.strptime(cert['notBefore'], '%b %d %H:%M:%S %Y %Z')
    not_after = datetime.datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
    
    print(f"Subject: {dict(x[0] for x in cert['subject'])}")
    print(f"Issuer: {dict(x[0] for x in cert['issuer'])}")
    print(f"Valid from: {not_before}")
    print(f"Valid until: {not_after}")
    print(f"Serial Number: {cert['serialNumber']}")
    
    # Check if certificate is valid
    now = datetime.datetime.now()
    if now < not_before:
        print("CERTIFICATE NOT YET VALID!")
    elif now > not_after:
        print("CERTIFICATE IS EXPIRED!")
    else:
        print("CERTIFICATE IS CURRENTLY VALID")
    
    # Print SAN (Subject Alternative Names)
    for ext in cert.get('subjectAltName', []):
        print(f"SAN: {ext}")

if __name__ == "__main__":
    hostname = "your-datafusion-endpoint.com"  # Replace with your actual endpoint
    try:
        cert = get_certificate_details(hostname)
        print_cert_info(cert)
    except ssl.SSLCertVerificationError as e:
        print(f"SSL Certificate Verification Error: {e}")
    except Exception as e:
        print(f"Error: {e}")
```

### 6. Using certifi with your Data Fusion API

```python
import requests
import certifi
import json

def call_datafusion_api(url, method='PUT', headers=None, data=None):
    """Call Data Fusion API with certifi's certificate bundle"""
    
    if headers is None:
        headers = {'Content-Type': 'application/json'}
    
    try:
        # Use certifi's certificate bundle for verification
        if method.upper() == 'PUT':
            response = requests.put(
                url, 
                headers=headers, 
                data=json.dumps(data) if data else None,
                verify=certifi.where()
            )
        elif method.upper() == 'GET':
            response = requests.get(
                url,
                headers=headers,
                verify=certifi.where()
            )
        # Add other methods as needed
        
        return response
    except requests.exceptions.SSLError as e:
        print(f"SSL Error: {e}")
        # You might want to inspect the certificate directly if verification fails
        # or return the error for handling by the caller
        raise

# Example usage
url = "https://your-datafusion-endpoint.com/v3/namespaces/default/profiles/dataproc"
headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_TOKEN_HERE'  # Replace with your auth token
}
data = {
    "name": "dataproc",
    "description": "Dataproc profile",
    # Add other required fields for your profile
}

try:
    response = call_datafusion_api(url, method='PUT', headers=headers, data=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"API call failed: {e}")
```

### Common use cases for certifi

1. **Ensuring consistent certificate verification across different platforms**
2. **Using the latest trusted root certificates in your application**
3. **Troubleshooting SSL certificate issues by ensuring you're using a trusted, up-to-date certificate bundle**
4. **Custom SSL contexts that require a specified CA bundle path**

## Advanced: Adding custom certificates to work with certifi

If you need to use your own certificates alongside certifi's bundle:

```python
import certifi
import tempfile
import shutil
import os
import requests

def create_custom_ca_bundle(custom_cert_path):
    """Create a custom CA bundle that includes certifi's certs plus your own"""
    
    # Create a temporary file
    temp_fd, temp_path = tempfile.mkstemp()
    
    try:
        # Copy certifi's CA bundle to the temp file
        with open(certifi.where(), 'rb') as certifi_file:
            os.write(temp_fd, certifi_file.read())
        
        # Append your custom certificate
        with open(custom_cert_path, 'rb') as custom_cert_file:
            os.write(temp_fd, b'\n')  # Ensure there's a newline between certs
            os.write(temp_fd, custom_cert_file.read())
            
        return temp_path
    finally:
        os.close(temp_fd)  # Close the file descriptor

# Example usage
custom_cert_path = '/path/to/your/custom_cert.pem'
custom_bundle_path = create_custom_ca_bundle(custom_cert_path)

try:
    # Use the custom bundle for your request
    response = requests.get('https://your-datafusion-endpoint.com', verify=custom_bundle_path)
    print(f"Status: {response.status_code}")
finally:
    # Clean up the temporary file
    os.unlink(custom_bundle_path)
```

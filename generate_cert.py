from cryptography import x509 #create and manage certificates
from cryptography.x509.oid import NameOID #provides predefined fields like country,state ,organization
from cryptography.hazmat.primitives import hashes, serialization #hashes-used for signing certificate
#serialization--used to save key/certificate to file
from cryptography.hazmat.primitives.asymmetric import rsa
#used to generate RSA public private key pair
import datetime #certicate validity period

key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
#rsa key--encrypt nd sign certificate
subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, "IN"),
    x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Karnataka"),
    x509.NameAttribute(NameOID.LOCALITY_NAME, "Bangalore"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, "ChatApp"),
    x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
])

cert = x509.CertificateBuilder().subject_name(subject).issuer_name(issuer)    .public_key(key.public_key())    .serial_number(x509.random_serial_number())    .not_valid_before(datetime.datetime.utcnow())    .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))    .sign(key, hashes.SHA256())

with open("key.pem", "wb") as f:
    f.write(key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ))

with open("cert.pem", "wb") as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))
#saves cert in PEM format
print("Certificates generated!")

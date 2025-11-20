# VaniKeys Directory Service (VDS)

**Created**: 2025-11-17
**Status**: Strategic Design
**Focus**: Public key registry and lookup system (QR-code-like for cryptographic keys)

---

## 🎯 Core Concept

**The embedded pattern serves DUAL purposes:**

1. **Human-Readable Identifier** (direct value)
   - "This is Stanford 2025 student 042"

2. **Directory Pointer** (registry lookup)
   - → `https://registry.stanford.edu/did/042`
   - → Rich metadata, verification, status

**Just like:**
- **QR code** → scannable pattern → URL with data
- **Domain name** → human-readable → DNS with IP/records
- **ISBN** → readable number → book database entry
- **VaniKey pattern** → readable ID → registry with key metadata

---

## 🗂️ How It Works

### Example: University DID

**Student's DID:**
```
did:key:...STANFORD-2025-042...
```

**Function 1: DIRECT (human-readable)**
```
"This is a Stanford DID from 2025 cohort, ID 042"
→ No lookup needed for basic identification
```

**Function 2: REGISTRY LOOKUP (directory)**
```
→ https://registry.stanford.edu/did/042
→ Returns rich metadata about this DID
```

**Registry Response:**
```json
{
  "id": "042",
  "type": "student_credential",
  "institution": "Stanford University",
  "issued": "2025-09-01",
  "cohort": "Class of 2025",

  "status": "active",  // or "revoked", "expired"
  "revocation_check": "https://registry.stanford.edu/revoke/042",

  "public_metadata": {
    "name": "John Doe",  // if student allows
    "major": "Computer Science",
    "degree_level": "Bachelor of Science"
  },

  "credentials_issued": [
    {
      "type": "degree",
      "title": "BS Computer Science",
      "date": "2025-06-15",
      "verification": "https://registry.stanford.edu/verify/degree/042"
    }
  ],

  "contact": {
    "email": "johndoe@stanford.edu"  // if public
  },

  "privacy": {
    "public_profile": true,
    "show_name": true,
    "show_contact": false
  }
}
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│  VaniKeys Platform                                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────────────────────────────────┐       │
│  │  1. Key Generation Service                  │       │
│  │     - Generate keys with embedded patterns  │       │
│  │     - Consumer gacha OR enterprise batch    │       │
│  └─────────────────────────────────────────────┘       │
│                          │                               │
│                          ▼                               │
│  ┌─────────────────────────────────────────────┐       │
│  │  2. Directory Service (VDS)                 │       │
│  ├─────────────────────────────────────────────┤       │
│  │                                              │       │
│  │  A. Public Registry                         │       │
│  │     - registry.vanikeys.com/lookup/{id}     │       │
│  │     - Free tier (status, basic metadata)    │       │
│  │     - Search/browse by organization         │       │
│  │                                              │       │
│  │  B. Private Registries (Enterprise)         │       │
│  │     - keys.acme.com/api/{id}                │       │
│  │     - Org-controlled access                 │       │
│  │     - Custom domains                         │       │
│  │     - Self-hosted option                    │       │
│  │                                              │       │
│  │  C. Registry API                            │       │
│  │     - POST /register                        │       │
│  │     - PUT /update/{id}                      │       │
│  │     - POST /revoke/{id}                     │       │
│  │     - GET /lookup/{id}                      │       │
│  │     - GET /search?org=X&status=active       │       │
│  │                                              │       │
│  │  D. Web Interface                           │       │
│  │     - Key profile pages                     │       │
│  │     - Organization dashboards               │       │
│  │     - Analytics/usage stats                 │       │
│  │     - QR code generation                    │       │
│  └─────────────────────────────────────────────┘       │
│                          │                               │
│                          ▼                               │
│  ┌─────────────────────────────────────────────┐       │
│  │  3. Verification Service                    │       │
│  │     - Check revocation status               │       │
│  │     - Verify ownership                      │       │
│  │     - Check expiration                      │       │
│  │     - Audit trail logging                   │       │
│  └─────────────────────────────────────────────┘       │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 📋 Use Cases with Registry Lookups

### Use Case 1: SSH Key Access Control

**Server receives SSH connection:**
```bash
# Server sees key: ...ACME-ENG-042...
# Server queries internal registry
response=$(curl -s keys.acme.com/api/042)

# Check authorization
status=$(echo $response | jq -r '.status')
authorized=$(echo $response | jq -r '.authorized_for[]' | grep $(hostname))

if [ "$status" = "active" ] && [ ! -z "$authorized" ]; then
  echo "Access granted for $(echo $response | jq -r '.owner.name')"
  # Allow login
fi
```

**Registry Response:**
```json
{
  "id": "042",
  "status": "active",
  "owner": {
    "employee_id": "042",
    "name": "Alice Smith",
    "team": "Platform Engineering"
  },
  "authorized_for": [
    "api-prod-1.acme.com",
    "api-prod-2.acme.com"
  ],
  "restrictions": {
    "ip_allowlist": ["10.0.0.0/8"],
    "mfa_required": true
  }
}
```

---

### Use Case 2: Credential Verification

**Employer verifies graduate's credential:**
```python
# Credential signed by: did:key:...STANFORD-2025-042...
pattern = extract_pattern(credential.issuer_did)
institution = pattern.split('-')[0]  # "STANFORD"
student_id = pattern.split('-')[2]   # "042"

# Look up in registry
registry_url = f"https://registry.{institution.lower()}.edu/did/{student_id}"
metadata = requests.get(registry_url).json()

# Verify
assert metadata['status'] == 'active', "Credential revoked"
assert 'BS Computer Science' in metadata['credentials_issued'], "Invalid degree"

# Hire with confidence
```

---

### Use Case 3: Research Data Verification

**Peer reviewer checks data provenance:**
```bash
# Paper claims data signed with: ...CHEMLAB-CHEN-PROTEIN-042...
curl research.chem.stanford.edu/exp/042

# Returns:
{
  "experiment": {
    "title": "Protein Folding Dynamics under Heat Stress",
    "pi": "Dr. Jennifer Chen",
    "start_date": "2025-06-01",
    "status": "active"
  },
  "data_signed": [
    {
      "dataset_id": "PF042-RAW-001",
      "hash": "sha256:abc123...",
      "location": "s3://research-data/pf042/raw/"
    }
  ],
  "publications": [
    {
      "doi": "10.1234/nature.2025.5678",
      "status": "published"
    }
  ],
  "reproducibility": {
    "protocol": "https://protocols.io/view/protein-folding-042",
    "code": "https://github.com/stanford-chem/pf042"
  }
}

# Verify data integrity
gpg --verify dataset.tar.gz.sig
# Signature matches pattern → Data authentic ✓
```

---

## 🔒 Privacy Tiers

Organizations choose what to reveal publicly:

### Tier 1: Public Registry (FREE)

**What's Visible:**
```json
{
  "id": "042",
  "status": "active",  // or "revoked"
  "organization": "Stanford University",
  "issued": "2025-09-01",
  "type": "student_credential"
}
```

**Purpose**: Just enough to verify key is valid
**Use Case**: QR-code-like scan → check status

---

### Tier 2: Verified Access (Requires Authentication)

**What's Visible:**
```json
{
  // ... Tier 1 data PLUS:
  "owner_name": "John Doe",
  "department": "Computer Science",
  "contact": "johndoe@stanford.edu",
  "credentials": ["BS CS"],
  "authorized_resources": [...]
}
```

**Authentication**: API key, OAuth, or organization membership
**Use Case**: Internal tools, partner integrations

---

### Tier 3: Private/Self-Hosted

**What's Visible:**
```json
{
  // ... All data:
  "ssn_hash": "...",
  "internal_notes": "...",
  "performance_reviews": [...],
  "audit_logs": [...]
}
```

**Hosting**: Organization runs own registry instance
**Use Case**: Highly regulated industries (healthcare, finance)

---

## 🔌 Integration Examples

### SSH Server Integration

```bash
# /etc/ssh/sshd_config
AuthorizedKeysCommand /usr/local/bin/vanikeys-lookup %k
AuthorizedKeysCommandUser vanikeys

# /usr/local/bin/vanikeys-lookup
#!/bin/bash
KEY_PATTERN=$(extract_pattern "$1")
REGISTRY="https://keys.acme.com/api"

# Look up key metadata
RESPONSE=$(curl -s "$REGISTRY/$KEY_PATTERN")
STATUS=$(echo $RESPONSE | jq -r '.status')

if [ "$STATUS" = "active" ]; then
  # Check server authorization
  SERVER=$(hostname)
  AUTHORIZED=$(echo $RESPONSE | jq -r ".authorized_for[] | select(. == \"$SERVER\")")

  if [ ! -z "$AUTHORIZED" ]; then
    echo "# Access granted for $(echo $RESPONSE | jq -r '.owner.name')"
    echo "$1"  # Return the key
  fi
fi
```

---

### DID Verification Library

```python
class VaniKeysVerifier:
    def verify_credential(self, credential):
        # Extract DID pattern
        did = credential['issuer']
        pattern = self.extract_pattern(did)

        # Parse pattern
        parts = pattern.split('-')
        institution = parts[0]  # "STANFORD"
        cohort = parts[1]       # "2025"
        student_id = parts[2]   # "042"

        # Look up in registry
        registry_url = f"https://registry.{institution.lower()}.edu/did/{student_id}"
        metadata = requests.get(registry_url).json()

        # Verify
        if metadata['status'] != 'active':
            raise ValueError("Credential revoked")

        if credential['type'] not in metadata['credentials_issued']:
            raise ValueError("Credential type not issued to this DID")

        return {
            'valid': True,
            'institution': metadata['institution'],
            'issued_date': metadata['issued'],
            'metadata': metadata
        }
```

---

### Certificate Verification Extension

```python
def verify_cert_with_vanikeys(cert):
    # Extract fingerprint pattern
    fingerprint = get_cert_fingerprint(cert)
    pattern = extract_pattern(fingerprint)

    # Parse pattern: PROD-API-2025-11-17-042
    env, purpose, date, serial = pattern.split('-')

    # Look up in CA registry
    registry_url = f"https://certs.globalSign.com/api/{serial}"
    metadata = requests.get(registry_url).json()

    # Verify
    assert metadata['status'] == 'active', "Certificate revoked"
    assert metadata['environment'] == env, "Environment mismatch"
    assert not metadata['expired'], "Certificate expired"

    # Additional checks
    if env == "PROD":
        assert cert.check_production_standards(), "Prod cert doesn't meet standards"

    return metadata
```

---

## 📱 QR Code Integration

### Generate QR Code for Key Pattern

```python
import qrcode

def generate_key_qr(key_pattern):
    # Pattern: STANFORD-2025-042
    registry_url = f"https://registry.stanford.edu/did/{key_pattern.split('-')[2]}"

    # Generate QR code pointing to registry
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(registry_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    return img
```

**Use Cases:**
- **Business cards**: Print QR code with DID pattern
- **Credentials**: Embed QR in diploma/certificate
- **Conference badges**: Scan to verify attendee

**Scan Flow:**
```
1. User scans QR code on business card
2. QR → https://registry.stanford.edu/did/042
3. Browser shows profile:
   - Name: John Doe
   - Degree: BS Computer Science, Stanford 2025
   - LinkedIn: ...
   - Portfolio: ...
4. Verify credential authenticity
```

---

## 🌐 Standards Alignment

### W3C DID Documents

```json
{
  "@context": "https://www.w3.org/ns/did/v1",
  "id": "did:key:...STANFORD-2025-042...",
  "verificationMethod": [...],

  "service": [{
    "id": "did:key:...STANFORD-2025-042...#registry",
    "type": "VaniKeysRegistry",
    "serviceEndpoint": "https://registry.stanford.edu/did/042"
  }]
}
```

---

### X.509 Certificate Extensions

```
Subject Alternative Name:
  URI: https://keys.acme.com/api/042

Custom Extension (VaniKeys Registry):
  OID: 1.3.6.1.4.1.XXXXX.1
  Value: https://keys.acme.com/api/042
```

---

## 💰 Business Models

### Model 1: Free Public Registry

**Offering:**
- Generate vanity key: $5-50 (one-time)
- Register in public directory: FREE
- Basic profile page: FREE
- QR code: FREE

**Premium Profile ($5-10/month):**
- Custom profile page
- Link to website/portfolio
- Analytics (who looked up your key)
- Verified badge

**Revenue**: Low per user, but viral potential

---

### Model 2: Enterprise Private Registry

**Setup Fee**: $5K-50K
- Batch key generation
- Pattern templates
- Dedicated account manager

**Annual License**: $10K-100K/year
- Private registry hosting
- API access (unlimited)
- Custom domain (keys.acme.com)
- SLA guarantees
- Audit logs
- User management

**Add-ons**:
- Self-hosted registry: +$20K-50K
- Professional services: $150-300/hour

**Revenue**: High ACV, predictable

---

### Model 3: Directory-as-a-Service (DaaS)

**The Product**: Organizations pay to HOST their key registries on VaniKeys infrastructure

**Like:**
- Docker Hub (container registry)
- npm (package registry)
- GitHub (code registry)
- **VaniKeys** (key registry)

**Pricing Tiers:**

**Startup** ($500-1K/month):
- 1,000 keys
- Public registry
- API access
- Basic analytics

**Business** ($2K-5K/month):
- 10,000 keys
- Private registry
- Custom domain
- Advanced analytics

**Enterprise** ($10K-50K/month):
- Unlimited keys
- Multi-region hosting
- Self-hosted option
- White-label
- 24/7 support

**Revenue Potential**: $1M-$10M ARR with 50-200 customers

---

## 🔧 API Specification

### Register Key

```http
POST /api/v1/register
Content-Type: application/json
Authorization: Bearer {api_key}

{
  "key_pattern": "STANFORD-2025-042",
  "key_type": "ed25519",
  "public_key": "...",
  "metadata": {
    "student_name": "John Doe",
    "degree": "BS Computer Science",
    "graduation_date": "2025-06-15"
  },
  "privacy_settings": {
    "public_profile": true,
    "show_name": false
  }
}

Response:
{
  "registry_id": "reg_stanford_042",
  "registry_url": "https://registry.stanford.edu/did/042",
  "qr_code_url": "https://registry.stanford.edu/qr/042.png",
  "status": "active"
}
```

---

### Lookup Key

```http
GET /api/v1/lookup/{pattern}

Response (Public):
{
  "id": "042",
  "status": "active",
  "organization": "Stanford University",
  "issued": "2025-09-01",
  "type": "student_credential",
  "revocation_check": "https://registry.stanford.edu/revoke/042"
}

Response (Authenticated):
{
  // ... Public data PLUS:
  "owner_name": "John Doe",
  "contact": "johndoe@stanford.edu",
  "credentials_issued": [...]
}
```

---

### Revoke Key

```http
POST /api/v1/revoke
Authorization: Bearer {api_key}

{
  "key_pattern": "STANFORD-2025-042",
  "reason": "Credential withdrawn",
  "effective_date": "2025-11-17"
}

Response:
{
  "status": "revoked",
  "revocation_date": "2025-11-17T10:00:00Z",
  "reason": "Credential withdrawn"
}
```

---

### Search Keys

```http
GET /api/v1/search?org=stanford&cohort=2025&status=active

Response:
{
  "total": 10000,
  "results": [
    {
      "pattern": "STANFORD-2025-001",
      "status": "active",
      "issued": "2025-09-01"
    },
    ...
  ],
  "pagination": {
    "page": 1,
    "per_page": 100,
    "total_pages": 100
  }
}
```

---

## 🎯 Implementation Phases

### Phase 1: Public Registry (8 weeks)

**Features:**
- Key registration API
- Public lookup endpoint
- Basic web interface
- QR code generation

**Deliverables:**
- Consumer can register pattern
- Anyone can look up status
- Profile pages live

---

### Phase 2: Enterprise Features (12 weeks)

**Features:**
- Private registries
- Custom domains
- Batch registration
- Advanced privacy controls

**Deliverables:**
- Stanford can host registry.stanford.edu
- Batch import 10K DIDs
- Tier-based privacy

---

### Phase 3: Self-Hosted Option (16 weeks)

**Features:**
- Self-hosted registry software
- Docker deployment
- Enterprise support
- Migration tools

**Deliverables:**
- Organizations can run own registry
- Data sovereignty
- Air-gapped deployments

---

## 📊 Success Metrics

### Consumer Metrics

- Registry lookups per day
- QR code scans per day
- Profile page views
- Premium profile conversions

### Enterprise Metrics

- Orgs using private registry
- Keys registered per org
- API calls per day
- Registry uptime (SLA)

### Revenue Metrics

- MRR from premium profiles
- ARR from enterprise contracts
- DaaS subscription revenue

---

## 🔗 Next Steps

1. **Build MVP public registry** (4 weeks)
2. **Pilot with Stanford** (DID issuance)
3. **Pilot with tech company** (SSH keys)
4. **Iterate based on feedback**
5. **Launch enterprise DaaS**

---

**Created**: 2025-11-17
**Session**: drifting-quasar-1117
**Status**: Ready for implementation
**Next**: Build public registry MVP

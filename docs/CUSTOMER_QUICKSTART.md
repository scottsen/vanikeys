# VaniKeys Customer Quick Start Guide

**Get your vanity SSH keys without ever sharing your private keys**

---

## What is VaniKeys?

VaniKeys generates **vanity SSH keys** - SSH keys with recognizable patterns in their fingerprints. Perfect for:

- **DevOps teams**: Branded keys for your organization (`acme-dev`, `team-alpha`)
- **Security**: Easily identify keys at a glance
- **Compliance**: Audit-friendly, traceable credentials
- **Team management**: Bulk key generation for onboarding

**Example vanity fingerprints:**
```
SHA256:lab123xxxxxxxxxxxxxxxxxxxxxxxxx
SHA256:acmecorpxxxxxxxxxxxxxxxxxxxxxxxxx
SHA256:dev001xxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## Why VaniKeys is Different

### ❌ Traditional Vanity Key Services (Don't Use!)

```
You → "I want vanity key" → Service generates keys → Service sends private key
                                                     ↑
                                              THEY KNOW YOUR PRIVATE KEY! 🚨
```

**Problem**: They must know your private key to find vanity patterns. Unacceptable for real security.

### ✅ VaniKeys Zero-Knowledge Protocol

```
You → "I want vanity key" → VaniKeys finds path → You derive key locally
                                                     ↑
                                         YOUR PRIVATE KEY NEVER LEAVES YOUR MACHINE ✓
```

**How it works:**
1. You keep a secret seed (never shared with anyone)
2. VaniKeys searches millions of "paths" to find one that produces a vanity pattern
3. VaniKeys tells you which path to take
4. You use your seed + path to generate the key **on your machine**
5. VaniKeys never sees your private key!

**Result**: You get the computational power of VaniKeys without the trust risk.

---

## Quick Start: Get Your First Vanity Key

### Step 1: Install VaniKeys CLI

```bash
pip install vanikeys-client
```

Requirements: Python 3.8+

### Step 2: Initialize Your Seed

```bash
vanikeys init
```

**What happens:**
- Generates a secure random seed (stays on your machine)
- Encrypts seed with your password
- Saves to `~/.vanikeys/seed.enc`
- Creates root public key (shared with VaniKeys)

**Important**: Your seed is **never transmitted** to VaniKeys. Back it up securely!

```bash
# Backup your encrypted seed
cp ~/.vanikeys/seed.enc ~/backup/vanikeys-seed-backup.enc
```

### Step 3: Order Your Vanity Key

```bash
vanikeys order ssh --pattern "dev123"
```

**Output:**
```
Order created: ord_abc123xyz
Pattern: dev123
Difficulty: Medium (~30 seconds)
Cost: $2.50
Status: Searching...

You can check status with: vanikeys status ord_abc123xyz
```

### Step 4: Check Order Status

```bash
vanikeys status ord_abc123xyz
```

**While searching:**
```
Order: ord_abc123xyz
Status: SEARCHING
Progress: 2.5M / ~10M paths (25%)
Elapsed: 12 seconds
```

**When found:**
```
Order: ord_abc123xyz
Status: FOUND ✓
Path: 8472615
Fingerprint: SHA256:dev123xxxxxxxxxxxxxxxxxxxxxxxxx
Public Key: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5...
```

### Step 5: Verify & Derive Your Key

```bash
# Verify the proof (automatic)
vanikeys verify ord_abc123xyz
# ✓ Proof valid
# ✓ Path produces claimed fingerprint
# ✓ Safe to derive

# Derive your private key locally
vanikeys derive ord_abc123xyz --output ~/.ssh/dev_key
```

**What happens:**
- Reads your encrypted seed (prompts for password)
- Applies the path VaniKeys found (8472615)
- Generates private key **on your machine**
- Saves to `~/.ssh/dev_key` (private) and `~/.ssh/dev_key.pub` (public)

**Verify the fingerprint:**
```bash
ssh-keygen -lf ~/.ssh/dev_key.pub
# 256 SHA256:dev123xxxxxxxxxxxxxxxxxxxxxxxxx no comment (ED25519)
```

### Step 6: Use Your Key

```bash
# Add to SSH agent
ssh-add ~/.ssh/dev_key

# Add to server
ssh-copy-id -i ~/.ssh/dev_key.pub user@server

# Use it
ssh -i ~/.ssh/dev_key user@server
```

---

## Enterprise: Bulk Key Generation

### Scenario: Onboard 50 Developers

**Goal**: Each developer gets a vanity key with pattern "acme-dev".

#### Option 1: Individual Orders (Each Developer)

```bash
# Each developer runs:
vanikeys init  # Their own seed
vanikeys order ssh --pattern "acme-dev"
vanikeys derive <order-id> --output ~/.ssh/id_acme
```

**Pros**: Maximum security (each person has unique seed)
**Cons**: Requires coordination, 50 separate orders

#### Option 2: Bulk Order (DevOps Manager)

```bash
# Manager orders 50 keys at once
vanikeys order bulk \
  --pattern "acme-dev" \
  --quantity 50 \
  --output acme-team-keys.json

# VaniKeys finds 50 different paths producing "acme-dev" pattern
# Returns: acme-team-keys.json with all paths
```

**Distribute to team:**
```bash
# Each team member:
vanikeys init  # Their own seed

# Import the bulk order
vanikeys import acme-team-keys.json

# Derive their assigned key (index 0-49)
vanikeys derive --bulk acme-team-keys.json --index 0 --output ~/.ssh/id_acme
```

**Pros**: Single order, volume discount, fast distribution
**Cons**: All keys derived from same root (recommend Option 1 for production)

#### Option 3: Hybrid (Recommended)

```bash
# Manager orders 50 keys with unique patterns
vanikeys order bulk \
  --pattern-template "acme-dev-{001..050}" \
  --output acme-team-keys.json

# Each team member gets uniquely identifiable key:
# SHA256:acmedev001xxxxxxxxxxxxxxxxxxxxxxxxx
# SHA256:acmedev002xxxxxxxxxxxxxxxxxxxxxxxxx
# ...
```

**Best of both worlds**: Unique patterns, audit trail, bulk pricing.

---

## Pricing & Pattern Difficulty

### Pattern Difficulty

The longer your pattern, the harder it is to find (exponentially harder).

| Pattern Length | Difficulty | Typical Time | Cost |
|----------------|------------|--------------|------|
| 3 characters   | Trivial    | < 1 second   | $0.50 |
| 4 characters   | Easy       | ~2 seconds   | $1.00 |
| 5 characters   | Medium     | ~30 seconds  | $2.50 |
| 6 characters   | Hard       | ~30 minutes  | $10.00 |
| 7 characters   | Very Hard  | ~20 hours    | $50.00 |
| 8+ characters  | Extreme    | Days/weeks   | Custom |

**Estimate before ordering:**
```bash
vanikeys estimate --pattern "mycompany"
# Pattern: mycompany (9 chars)
# Difficulty: Extreme
# Expected time: ~14 days
# Estimated cost: $250.00
# Recommendation: Try shorter pattern (e.g., "myco" = $2.50)
```

### Pricing Tiers

- **Pay-as-you-go**: $0.50 - $50 per key (based on difficulty)
- **Team plan**: $100/month, 50 keys included, $1.50/key after
- **Enterprise**: Custom pricing, volume discounts, dedicated compute

**Bulk discounts:**
- 10-49 keys: 10% off
- 50-99 keys: 20% off
- 100+ keys: 30% off

---

## Security Best Practices

### Seed Management

**Your seed is your master secret**. Protect it like a root password.

✅ **DO:**
- Back up encrypted seed securely (offline, encrypted backups)
- Use strong password for seed encryption
- Store in secure location (`~/.vanikeys/seed.enc` has restricted permissions)
- Consider hardware token storage (Yubikey, TPM) for production

❌ **DON'T:**
- Share your seed with anyone (not even VaniKeys!)
- Store seed unencrypted
- Use weak password for seed encryption
- Store backups in plaintext

### Key Rotation

Even with vanity keys, rotate periodically:

```bash
# Generate new seed for rotation
vanikeys init --rotate

# Order new vanity keys
vanikeys order ssh --pattern "dev123"

# Deploy new keys
# Remove old keys from servers
```

### Audit Trail

VaniKeys provides full audit logs:

```bash
vanikeys history
# Order ID       | Pattern   | Date       | Status
# ord_abc123xyz  | dev123    | 2025-12-01 | COMPLETED
# ord_def456xyz  | acme-dev  | 2025-12-02 | COMPLETED
```

Export for compliance:
```bash
vanikeys history --export audit-2025-12.json
```

---

## Troubleshooting

### "Seed file not found"

```bash
vanikeys init  # Initialize if first time
```

### "Wrong password"

Seed password incorrect. Try again or restore from backup.

### "Order not found"

Check order ID typo, or order may have expired (30 days).

### "Derivation verification failed"

**DO NOT PROCEED**. This indicates:
- Corrupted data
- Man-in-the-middle attack
- Bug in VaniKeys

Contact support: security@vanikeys.dev

### "Pattern too difficult"

Try shorter pattern or wait longer. 8+ character patterns can take days.

---

## FAQ

### Q: Does VaniKeys ever see my private key?

**No.** Your private key is derived on your machine from your seed + the path VaniKeys found. VaniKeys only sees your public key and derivation paths.

### Q: What if VaniKeys gets hacked?

**Your keys are safe.** Even with full access to VaniKeys servers, attackers cannot derive your private keys (they don't have your seed).

### Q: Can I use vanity keys for production?

**Yes!** VaniKeys zero-knowledge protocol is production-grade. The keys are cryptographically identical to standard SSH keys, just with recognizable fingerprints.

### Q: What key types are supported?

Currently: **Ed25519** (recommended, fast, modern)

Coming soon: RSA-4096, ECDSA, GPG keys

### Q: Can I transfer my seed to another machine?

**Yes.** Copy `~/.vanikeys/seed.enc` to new machine, then use `vanikeys` as normal. Ensure secure transfer (encrypted channel).

### Q: What happens if I lose my seed?

**You lose access to ordered vanity paths.** You can't derive the keys without the seed. **Back up your seed!**

You can create a new seed (`vanikeys init`) and order new keys, but old orders are unrecoverable.

### Q: Do patterns have to be at the start of the fingerprint?

**No.** Patterns can appear anywhere in the fingerprint (substring match). Prefix matching is faster but VaniKeys supports both.

### Q: Can I use special characters in patterns?

Basic patterns: Letters and numbers (`a-z`, `0-9`)
Advanced: Regex support for complex patterns (e.g., `dev[0-9]{3}`)

### Q: How do I know VaniKeys isn't lying about the path?

**Cryptographic proofs.** Before deriving, `vanikeys verify` checks:
1. Path produces claimed public key
2. Fingerprint matches pattern
3. VaniKeys signature valid

If verification fails, DON'T derive.

---

## Support & Contact

- **Documentation**: https://docs.vanikeys.dev
- **Technical Support**: support@vanikeys.dev
- **Security Issues**: security@vanikeys.dev (PGP key on website)
- **Sales/Enterprise**: sales@vanikeys.dev

---

## What's Next?

- **Try it**: Generate your first vanity key (free tier: 3 keys/month)
- **Team pilot**: Test with your DevOps team (14-day trial)
- **Enterprise demo**: Schedule demo for bulk deployment

```bash
# Sign up & get started
vanikeys register
vanikeys order ssh --pattern "test"
```

**Welcome to secure, verifiable vanity key generation!** 🔑

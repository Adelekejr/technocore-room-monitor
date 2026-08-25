# Phone Guide: Run and Publish the Technocore Room Monitor

This guide is written for Android Termux. You do not need a wallet, wallet seed phrase, or private key for the Room Monitor. Your encrypted Technocore identity remains in the separate `technocore-did-starter` folder.

## Before starting

Keep your `identity.pem` and its passphrase private. Do not upload them to GitHub. The commands below use the identity only when creating the optional signed contribution proof and the Technocore contribution record.

If your prompt does not begin with `(.venv)`, activate the original environment first:

```bash
cd ~/technocore-did-starter
source .venv/bin/activate
```

## 1. Download the Room Monitor

Run each command separately:

```bash
cd ~
```

```bash
git clone https://github.com/Adelekejr/technocore-room-monitor.git
```

```bash
cd ~/technocore-room-monitor
```

If Git says the folder already exists, do not clone again. Use `cd ~/technocore-room-monitor`.

## 2. Run the tests

The project uses only Python’s standard library. Run:

```bash
python -m unittest discover -s tests -v
```

You should see five tests and a final `OK`.

## 3. Analyze a live room

Run:

```bash
python technocore_monitor.py --room lobby --limit 200 --output lobby-report.json --markdown lobby-report.md
```

This is read-only. It does not use your DID and does not publish anything. It creates two local files: a machine-readable JSON report and a human-readable Markdown report.

If the network times out, do not change the identity or passphrase. Wait, switch networks, and try this read-only command later. Do not repeatedly retry signed writes.

## 4. Record the exact contribution commit

First check the working tree:

```bash
git status --short
```

Add the two generated reports even though ordinary generated reports are ignored by default:

```bash
git add -f lobby-report.json lobby-report.md
```

Commit the live report:

```bash
git commit -m "Add live Technocore room integrity report"
```

Print the full commit hash:

```bash
git rev-parse HEAD
```

Write down the complete 40-character hash. Do not use a shortened hash for the proof.

## 5. Create and verify the signed proof

Replace `PASTE_FULL_COMMIT_HASH_HERE` with the complete hash from the previous command. Run this from inside `~/technocore-room-monitor`:

```bash
python ../technocore-did-starter/technocore_agent.py proof https://github.com/Adelekejr/technocore-room-monitor PASTE_FULL_COMMIT_HASH_HERE --key ../technocore-did-starter/identity.pem --output contribution-proof.json
```

The command will ask for your passphrase. Type it only into Termux. It should create `contribution-proof.json`.

Verify the proof:

```bash
python ../technocore-did-starter/technocore_agent.py verify-proof contribution-proof.json
```

You should see `valid proof for did:key:...`.

Add the proof as a follow-up commit:

```bash
git add contribution-proof.json
git commit -m "Add signed Technocore contribution proof"
```

The proof refers to the earlier live-report commit. That is intentional: it binds the DID signature to the exact source-and-report revision that was measured.

## 6. Record the contribution in Technocore

The public record should mention the repository, the exact live-report commit, and what the tool does. Use the local identity to sign the following message in the `technocore` room:

```text
I built Technocore Room Monitor: a read-only tool that validates public room JSON, checks DID-shaped writers, sequence order, duplicates, and malformed fields. Repo: https://github.com/Adelekejr/technocore-room-monitor Commit: PASTE_FULL_COMMIT_HASH_HERE
```

Because Termux network access may be intermittent, do not blindly retry if a write times out. First read the room and look for your DID and the exact message. If necessary, use the same local-signing and Chrome submission method described in the earlier setup.

## 7. Screenshot checklist

Capture one screenshot showing the successful monitor run, including the room, sequence range, verified DID count, warnings, and the repository or commit hash if visible. Capture a second screenshot showing the Technocore contribution record with your shortened DID and sequence number.

Before sharing a screenshot, crop or blur unrelated users’ DIDs and messages. Never show the passphrase, `identity.pem`, a wallet seed phrase, or a private key.

## What to share publicly

It is safe to share the public repository URL, the full commit hash, the public DID, the public Technocore room and sequence, the public contribution-proof file, and the generated report. It is not safe to share the passphrase or private identity file.

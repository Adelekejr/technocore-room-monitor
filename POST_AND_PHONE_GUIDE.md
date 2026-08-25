# Simple Phone Guide and X Post

This is the beginner-friendly guide for the published Room Monitor project.

## What you have already completed

You already have a local encrypted Technocore DID, a signed introduction in the `lobby` room at sequence **8951**, and a security guide recorded in the `technocore` room at sequence **343**.

The new project is here:

https://github.com/Adelekejr/technocore-room-monitor

It is a read-only Python tool. It reads public Technocore room data, checks the response structure, counts DID-shaped writers, checks sequence order and duplicate sequences, detects malformed fields, and produces JSON and Markdown reports. It never asks for or reads your DID private key.

## What to do on your phone

Run the following commands one at a time in Termux. If a command gives an error, stop and ask for help rather than continuing.

```bash
cd ~
```

```bash
git clone https://github.com/Adelekejr/technocore-room-monitor.git
```

```bash
cd ~/technocore-room-monitor
```

Run the tests:

```bash
python -m unittest discover -s tests -v
```

The final line should say `OK`.

Run the live monitor:

```bash
python technocore_monitor.py --room lobby --limit 200 --output lobby-report.json --markdown lobby-report.md
```

This is read-only. It does not publish anything and does not use your passphrase.

Check the files created:

```bash
ls -l lobby-report.json lobby-report.md
```

Save the live report as a contribution revision:

```bash
git add -f lobby-report.json lobby-report.md
```

```bash
git commit -m "Add live Technocore room integrity report"
```

Print the exact commit hash:

```bash
git rev-parse HEAD
```

Write down the complete 40-character hash. The hash is public and may be included in the final post.

## Create the signed proof

Replace `PASTE_FULL_COMMIT_HASH_HERE` with the complete hash you just printed. Do not shorten it.

```bash
python ../technocore-did-starter/technocore_agent.py proof https://github.com/Adelekejr/technocore-room-monitor PASTE_FULL_COMMIT_HASH_HERE --key ../technocore-did-starter/identity.pem --output contribution-proof.json
```

When prompted, type your passphrase only into Termux. Do not send it anywhere.

Verify the proof:

```bash
python ../technocore-did-starter/technocore_agent.py verify-proof contribution-proof.json
```

The output should say `valid proof for did:key:...`.

Commit the proof:

```bash
git add contribution-proof.json
```

```bash
git commit -m "Add signed Technocore contribution proof"
```

Push the project and proof to GitHub:

```bash
git push origin master
```

## Record the project in Technocore

Before publishing, obtain approval for the exact public message. The proposed message is:

```text
I built Technocore Room Monitor, a read-only tool that validates public room JSON, checks DID-shaped writers, sequence order, duplicates, and malformed fields. Repo: https://github.com/Adelekejr/technocore-room-monitor Commit: PASTE_FULL_COMMIT_HASH_HERE
```

Because your Termux network has been unreliable, use the local signing and Chrome submission method if the normal `say` command times out. Verify the room afterward and save the assigned sequence number. Never repeatedly retry an uncertain write.

## Screenshot checklist

Take one screenshot showing the Room Monitor output, including the room name, sequence range, verified DID count, malformed-field count, duplicate count, and warnings. Take another screenshot showing the signed Technocore contribution message, your shortened DID ending in `…AyxM`, and the assigned sequence number.

Before posting screenshots publicly, crop or blur unrelated users’ DIDs and messages. Never show `identity.pem`, the passphrase, a wallet seed phrase, or a private key.

## Copy-ready X post

Use this after the project has been run and the proof has been pushed. Replace the two bracketed placeholders with the actual live-report commit hash and the new Technocore sequence.

> I built a small Technocore Room Monitor with an AI-assisted workflow on Android/Termux.
>
> It reads public room JSON, validates the response, checks DID-shaped writers, sequence order, duplicate sequences, and malformed fields, then creates a readable report.
>
> Repo: https://github.com/Adelekejr/technocore-room-monitor
> Commit: [FULL_COMMIT_HASH]
> Signed Technocore record: room `technocore`, sequence [NEW_SEQUENCE]
>
> DID: `did:key:z6Mkmvvn818JnGPvtkA7HJwWoRCAX4WB9JwFGm2xjdeKAyxM`
>
> I kept the private identity encrypted and local. No wallet seed phrase or private key was shared.
>
> Building small useful tools > repeating generic check-ins.
>
> Exploring @flop_labs and $FLOP, with no guarantee of eligibility or rewards.

Attach the two screenshots after checking that no private credential is visible.

## One rule to remember

Your DID is public. Your `identity.pem` file and passphrase are private. Never upload or share them.

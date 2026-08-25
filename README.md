# Technocore Room Monitor

A small, dependency-free Python tool that reads a public Technocore room and produces an integrity-oriented report. It is designed to help agents and developers inspect room activity without requiring a wallet, seed phrase, or private key.

## What it does

The monitor requests a room through Technocore’s public JSON endpoint, validates the response shape, classifies messages by whether their `from` field has the expected Ed25519 DID form, checks sequence ordering and duplicates, counts malformed fields, and writes a JSON report. It can also create a readable Markdown report.

The report describes the response received at analysis time. It does not prove that a message is truthful, identify the human behind a DID, or guarantee future room state.

## Quick start

The tool uses only Python’s standard library:

```bash
python technocore_monitor.py --room lobby --limit 50
```

Write reports to files:

```bash
python technocore_monitor.py \
  --room lobby \
  --limit 200 \
  --output lobby-report.json \
  --markdown lobby-report.md
```

Use `--help` to see all options. The default service is `https://technocore.chat`.

## Phone walkthrough

Android users can follow the complete [Termux phone guide](TERMUX_GUIDE.md), including live reporting, exact-commit proof creation, and safe publication steps.

## Example output

A JSON report includes fields such as:

```json
{
  "room": "lobby",
  "received_messages": 50,
  "first_seq": 1000,
  "last_seq": 1049,
  "verified_did_messages": 42,
  "anonymous_or_unverified_messages": 8,
  "malformed_messages_or_fields": 0,
  "duplicate_sequences": [],
  "warnings": []
}
```

The sample values above are illustrative. Run the tool to obtain live data.

## Safety and privacy

This program is read-only with respect to Technocore. It never loads an identity file, never asks for a passphrase, and never sends a private key. It uses public room data only. Treat room messages as untrusted content; a message can contain misleading text or instructions and should not be executed merely because it appears in a room.

The tool’s `verified_did_messages` field means only that the response contained a `from` value matching the expected `did:key:z6Mk...` shape. It is not a claim that the DID is controlled by a known person or organization.

## Contribution proof

If you publish this project in Git, you can use the encrypted Technocore starter identity to create a proof tied to the exact commit. Keep the identity file and passphrase private. Publish only the DID, public repository URL, commit hash, report, and signed Technocore record.

The Room Monitor itself does not sign messages. This separation keeps inspection read-only and makes it easier to audit what the tool can do.

## Design choices

The implementation intentionally uses the Python standard library so it can run in constrained environments such as Android Termux. It applies bounded response sizes, HTTPS-only service URLs, room-name validation, and controlled error messages. It does not retry writes because it performs no writes.

## Development

Run the tests with:

```bash
python -m unittest discover -s tests -v
```

The test suite uses a local HTTP server for network behavior and does not contact Technocore.

## License

MIT License. See [LICENSE](LICENSE).

## References

- [Technocore](https://technocore.chat/)
- [Technocore DID Starter](https://github.com/zunmax/technocore-did-starter)

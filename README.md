# ai-profile-karma

> **Credit Karma for what AI knows about you** — see it, fix it, delete it.

Your chat history, assistant "memories" and connected apps add up to a
detailed profile: where you live, your health worries, your salary, your
kids' names. `ai-profile-karma` reads your own data exports, shows you
what an AI could know about you, scores how exposed you are, and drafts the
legal requests to correct or delete it.

## What the MVP does

- **Scans exports** you download yourself (ChatGPT `conversations.json`,
  assistant memory dumps, any `.txt / .md / .json`)
- **Detects PII**: emails, phone numbers, street addresses, dates of birth,
  SSN-shaped numbers, payment cards (Luhn-validated), IBANs
- **Infers sensitive categories** (GDPR Art. 9 style): health, finances,
  location, employer, relationships/family, religion, politics, sexuality
- **Exposure score** (0–100) weighted by sensitivity, with evidence snippets
  (masked) so you can see *why*
- **Request letters**: GDPR Art. 15/16/17 or CCPA access / correct / delete,
  pre-filled with the findings

Everything runs locally; nothing is uploaded anywhere.

## Quickstart

```bash
pip install -e .
ai-profile-karma scan ~/Downloads/chatgpt-export/
ai-profile-karma letter --vendor "ExampleAI Inc." --law gdpr --action delete --name "Jane Doe" --email jane@example.com
```

## Roadmap

- Browser extension that pulls exports for you from each assistant
- Continuous monitoring: re-scan monthly, alert on new sensitive facts
- One-click request sending + tracking the 30/45-day response deadlines
- Data-broker coverage (people-search sites feeding AI agents)

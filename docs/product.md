# CyberSOS — Product

## Problem

When someone in India loses money to a UPI or financial fraud, the first
minutes matter — but the official reporting path (the National Cyber Crime
Reporting Portal and the 1930 helpline) is designed for filing a complaint,
not for helping a stressed, confused victim figure out what to do *right
now*. People lose time deciding what to do first, forget to preserve
evidence, and often under-report because the process feels intimidating.

## Target user

An Indian citizen, often not technical, who has just realized they've been
scammed — typically via UPI, a fraudulent bank transfer, a card, or a
compromised wallet. They are stressed, time-pressured, and need to know
what to do immediately, not a lecture on cybersecurity.

## Product goal

Give that person a calm, trustworthy layer that:

1. Helps them understand what happened
2. Flags how urgent it is
3. Tells them exactly what to do next
4. Helps them organize evidence as they go
5. Prepares the information they'll need for an official complaint
6. Points them to the correct official channels (1930, cybercrime.gov.in)
7. Lets them track the status of their own incident

CyberSOS is a citizen-support layer, not a replacement for the government's
own reporting systems — every response reinforces that distinction.

## Current MVP scope

- Financial fraud / UPI fraud guided questions
- Guided questions for other cyber crime and women/children related crime
- Landing page explaining the product and its limits
- A first step of the incident flow ("what happened?")
- An `incidents` record created in Postgres via the API
- Health checks for the API and the database
- Clean, independently runnable frontend and backend

## Intentionally out of scope (this phase)

- AI-driven question selection and drafting (the current question provider is deterministic)
- OCR or evidence/image analysis
- Real integration with banks, UPI providers, 1930, or cybercrime.gov.in
- Actual government complaint submission (the user still files through the official portal)
- Authentication and accounts
- Notifications
- Payment processing
- Multilingual support

These are all planned for later phases, once the foundation is stable.

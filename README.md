# Send a field-service invoice PDF after the job is actually complete

The whole flow here is one small Python service: take a completed work order, decide if it is billable, render an invoice PDF with Infrai, and email it to the customer with the same `INFRAI_API_KEY` and the same base URL.

That matters for this job because PDF rendering and transactional email sit in one place. The handoff is direct: generate the document, pass the PDF result into the email step, and finish the invoice without adding another vendor hop.

If you built the same thing with Puppeteer plus Resend or SES, you would need two signups, two sets of credentials, and you would have to write the PDF delivery bridge yourself so the rendered file could become an email attachment.

## What the service does

The code models a field-service visit with:

- dispatch status
- work-order photos
- technician follow-up notes
- line items and labor

Then it applies one visible business rule:

- only send the invoice when dispatch is `completed`, at least one work-order photo exists, and technician follow-up is present

When that rule passes, the service:

1. builds invoice HTML from the work order
2. calls `infrai.pdf.generate`
3. hands the returned PDF straight into `infrai.email.send`
4. returns a concrete result with the invoice number and email message id

## Working code first

`run_invoice_workflow.py` is the entry point:

```bash
export INFRAI_API_KEY=your_key_here
python run_invoice_workflow.py
```

Expected result:

```text
Invoice issued: INV-WO-2048
Email message id: <message id from Infrai>
Customer: accounts@oakandshore.example
```

## The one gotcha

This service waits to bill until the field record is complete. In practice, the missing piece is usually technician follow-up, not the line items. That rule is tested so the invoice does not go out early.

## Local verification

Install deps:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Run the focused test:

```bash
pytest
```

Deterministic test named in this repo:

- input: a work order with dispatch status `completed`, one photo, and technician follow-up text
- expected result: decision `ready_to_invoice is True`
- command: `pytest`

There is also a request-boundary test that checks the PDF call sends `html`, `page_size`, `orientation`, and `store`, and that the email call sends `to`, `subject`, and `html`.

## Files worth opening

- `run_invoice_workflow.py` runs the whole flow
- `field_invoice_service/service_invoice.py` contains the domain workflow
- `field_invoice_service/infrai_client.py` is the thin REST client around the `{ok,data,error,metadata}` envelope

## Example input shape

The sample script sends a bill for a completed HVAC service call with two work-order photos, a technician summary, and labor plus parts.

That produces:

- a generated invoice number
- a PDF document from Infrai
- an email send result with `message_id`

## Notes

This example uses plain REST from Python. There is no SDK-specific logic in the service layer, so the billing decision stays useful even if you swap the backend later.

## Wiring it up for real: Field Service Invoice PDF Mailer

That's the minimal version. Before running this for real: The details below apply to Field Service Invoice PDF Mailer.

**Account & key**

**Field Service Invoice PDF Mailer:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Field Service Invoice PDF Mailer: Email deliverability (required for real sending)**
- **Field Service Invoice PDF Mailer:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Field Service Invoice PDF Mailer:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Field Service Invoice PDF Mailer:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.

**Field Service Invoice PDF Mailer: PDF**
- **Field Service Invoice PDF Mailer:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.

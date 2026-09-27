from .infrai_client import infrai
from .models import InvoiceDecision, IssueInvoiceRequest, IssuedInvoice


def decide_invoice_ready(request: IssueInvoiceRequest) -> InvoiceDecision:
    work_order = request.work_order
    if work_order.dispatch.status != "completed":
        return InvoiceDecision(ready_to_invoice=False, reason="dispatch must be completed")
    if not work_order.photos:
        return InvoiceDecision(ready_to_invoice=False, reason="at least one work-order photo is required")
    if not work_order.technician_follow_up or not work_order.technician_follow_up.summary.strip():
        return InvoiceDecision(ready_to_invoice=False, reason="technician follow-up is required")
    return InvoiceDecision(ready_to_invoice=True, reason="ready to invoice")


def render_invoice_html(request: IssueInvoiceRequest, invoice_number: str) -> str:
    total_amount = sum(item.total for item in request.work_order.line_items)
    line_rows = "".join(
        f"<tr><td>{item.description}</td><td>{item.quantity}</td><td>${item.unit_price:.2f}</td><td>${item.total:.2f}</td></tr>"
        for item in request.work_order.line_items
    )
    photo_rows = "".join(
        f"<li>{photo.caption}: {photo.image_url}</li>"
        for photo in request.work_order.photos
    )
    follow_up = request.work_order.technician_follow_up.summary if request.work_order.technician_follow_up else ""

    return f"""
    <html>
      <body style=\"font-family: Arial, sans-serif; padding: 24px; color: #222;\">
        <h1>Field Service Invoice</h1>
        <p><strong>Invoice:</strong> {invoice_number}</p>
        <p><strong>Work order:</strong> {request.work_order.work_order_id}</p>
        <p><strong>Customer:</strong> {request.customer.name}</p>
        <p><strong>Service address:</strong> {request.customer.service_address}</p>
        <p><strong>Dispatch status:</strong> {request.work_order.dispatch.status}</p>
        <h2>Technician follow-up</h2>
        <p>{follow_up}</p>
        <h2>Work-order photos</h2>
        <ul>{photo_rows}</ul>
        <h2>Charges</h2>
        <table border=\"1\" cellspacing=\"0\" cellpadding=\"6\" width=\"100%\">
          <tr><th align=\"left\">Description</th><th>Qty</th><th>Unit</th><th>Total</th></tr>
          {line_rows}
        </table>
        <p style=\"margin-top: 16px; font-size: 18px;\"><strong>Total due: ${total_amount:.2f}</strong></p>
      </body>
    </html>
    """.strip()


def render_invoice_email_html(request: IssueInvoiceRequest, invoice_number: str, total_amount: float) -> str:
    return f"""
    <html>
      <body style=\"font-family: Arial, sans-serif; color: #222;\">
        <p>Hello {request.customer.name},</p>
        <p>Your field-service visit has been closed and invoice <strong>{invoice_number}</strong> is ready.</p>
        <p>Total due: <strong>${total_amount:.2f}</strong></p>
        <p>The PDF invoice was generated and attached in the same workflow that sent this email.</p>
      </body>
    </html>
    """.strip()


def issue_invoice_for_work_order(request: IssueInvoiceRequest) -> IssuedInvoice:
    decision = decide_invoice_ready(request)
    if not decision.ready_to_invoice:
        raise ValueError(f"Work order is not billable: {decision.reason}")

    invoice_number = f"INV-{request.work_order.work_order_id}"
    total_amount = round(sum(item.total for item in request.work_order.line_items), 2)

    pdf_html = render_invoice_html(request, invoice_number)
    pdf_env = infrai.pdf.generate(
        html=pdf_html,
        page_size="A4",
        orientation="portrait",
        store=False,
    )

    email_html = render_invoice_email_html(request, invoice_number, total_amount)
    email_env = infrai.email.send(
        to=request.customer.email,
        subject=f"Invoice {invoice_number} for completed service",
        html=email_html,
        attachments=[{"filename": f"{invoice_number}.pdf", "url": pdf_env["data"]["url"]}],
    )

    return IssuedInvoice(
        invoice_number=invoice_number,
        customer_email=request.customer.email,
        total_amount=total_amount,
        message_id=email_env["data"]["message_id"],
    )

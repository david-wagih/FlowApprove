# One (subject, body) per event the employee should hear about. Bodies are str.format templates
# filled from the event payload.
TEMPLATES = {
    "expense.submitted": (
        "We received your expense claim",
        "Hi {employee_name}, your claim for {amount} {currency} ({category}) was submitted and is "
        "waiting on your manager's approval.",
    ),
    "expense.approved": (
        "Your expense claim was approved",
        "Hi {employee_name}, your claim for {amount} {currency} was approved. The reimbursement is "
        "on its way.",
    ),
    "expense.rejected": (
        "Your expense claim was rejected",
        "Hi {employee_name}, your claim for {amount} {currency} was rejected. Reason: {reason}",
    ),
    "payment.completed": (
        "You've been reimbursed",
        "Hi {employee_name}, {amount} {currency} has been paid to your account (reference {reference}).",
    ),
    "payment.failed": (
        "Your reimbursement didn't go through",
        "Hi {employee_name}, we couldn't pay your {amount} {currency} reimbursement ({reason}). "
        "Finance has been notified and will retry.",
    ),
}

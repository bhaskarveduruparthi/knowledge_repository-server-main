from flask_mail import Mail, Message
from flask import current_app
from datetime import datetime
import os
import threading

mail = Mail()

# ─── Shared helpers ──────────────────────────────────────────────────────────

def _send_async(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            app.logger.error(f"Async email failed: {str(e)}")

def _dispatch(msg):
    """Fire-and-forget — sends email in background thread."""
    app = current_app._get_current_object()
    thread = threading.Thread(target=_send_async, args=(app, msg))
    thread.daemon = True
    thread.start()

def _year():
    return datetime.utcnow().year

def _logo_block(badge_label: str, badge_bg: str, badge_color: str, badge_border: str) -> str:
    return f"""
    <table cellpadding="0" cellspacing="0" border="0" width="100%">
      <tr>
        <td>
          <table cellpadding="0" cellspacing="0" border="0">
            <tr>
              <td style="background:rgba(255,255,255,0.15);border-radius:8px;padding:8px 14px;">
                <table cellpadding="0" cellspacing="0" border="0">
                  <tr>
                    <td style="width:36px;height:36px;background:rgba(255,255,255,0.2);border-radius:6px;
                                text-align:center;vertical-align:middle;
                                font-size:20px;font-weight:800;color:#ffffff;font-family:Arial,sans-serif;">
                      Y
                    </td>
                    <td style="padding-left:10px;vertical-align:middle;">
                      <div style="font-size:15px;font-weight:700;color:#ffffff;
                                  font-family:Arial,sans-serif;line-height:1.2;">
                        Yash Technologies
                      </div>
                      <div style="font-size:10px;color:rgba(255,255,255,0.65);
                                  letter-spacing:1.5px;text-transform:uppercase;
                                  font-family:Arial,sans-serif;">
                        Knowledge Repository
                      </div>
                    </td>
                  </tr>
                </table>
              </td>
              <td style="padding-left:16px;vertical-align:middle;">
                <span style="display:inline-block;padding:4px 14px;border-radius:12px;
                             font-size:11px;font-weight:700;letter-spacing:.5px;
                             text-transform:uppercase;font-family:Arial,sans-serif;
                             background:{badge_bg};color:{badge_color};border:1px solid {badge_border};">
                  {badge_label}
                </span>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
    """

def _footer_block() -> str:
    return f"""
    <table cellpadding="0" cellspacing="0" border="0" width="100%"
           style="background:#2d5f4f;border-radius:0 0 12px 12px;">
      <tr>
        <td style="padding:20px 36px;">
          <p style="margin:0;font-size:11px;color:rgba(255,255,255,0.6);
                    font-family:Arial,sans-serif;line-height:1.6;">
            This is an automated email from the Knowledge Repository Management System.<br>
            Please do not reply to this email.
          </p>
          <p style="margin:8px 0 0;font-size:11px;color:rgba(255,255,255,0.4);
                    font-family:Arial,sans-serif;">
            &copy; {_year()} Yash Technologies &nbsp;&middot;&nbsp; KR System
          </p>
        </td>
      </tr>
    </table>
    """

def _table_row(label: str, value: str, bg: str) -> str:
    return f"""
    <tr>
      <td style="padding:10px 14px;font-size:13px;font-weight:600;color:#2d5f4f;
                 font-family:Arial,sans-serif;width:38%;background:{bg};
                 border-bottom:1px solid #e8f0ed;">
        {label}
      </td>
      <td style="padding:10px 14px;font-size:13px;color:#333333;
                 font-family:Arial,sans-serif;background:{bg};
                 border-bottom:1px solid #e8f0ed;">
        {value}
      </td>
    </tr>
    """

def _status_pill(label: str, bg: str, color: str, border: str) -> str:
    return (f'<span style="display:inline-block;padding:3px 12px;border-radius:10px;'
            f'font-size:12px;font-weight:700;font-family:Arial,sans-serif;'
            f'background:{bg};color:{color};border:1px solid {border};">'
            f'{label}</span>')

def _cta_button(url: str, label: str, bg: str) -> str:
    return f"""
    <table cellpadding="0" cellspacing="0" border="0">
      <tr>
        <td style="border-radius:8px;background:{bg};">
          <a href="{url}"
             style="display:inline-block;padding:13px 30px;border-radius:8px;
                    font-size:14px;font-weight:700;text-decoration:none;
                    letter-spacing:.3px;color:#ffffff;font-family:Arial,sans-serif;
                    background:{bg};">
            {label}
          </a>
        </td>
      </tr>
    </table>
    """

def _divider() -> str:
    return """
    <table cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-bottom:20px;">
      <tr>
        <td style="height:1px;background:#c8e6c9;font-size:0;line-height:0;">&nbsp;</td>
      </tr>
    </table>
    """

def _table_header(title: str) -> str:
    return f"""
    <tr>
      <td colspan="2"
          style="background:#2d5f4f;color:#ffffff;font-size:11px;
                 text-transform:uppercase;letter-spacing:.8px;
                 padding:10px 14px;font-family:Arial,sans-serif;font-weight:700;">
        {title}
      </td>
    </tr>
    """

# ─── Template 1 — Approval Request (to IRM) ─────────────────────────────────

def send_repo_approval_email(irm_email, created_by, customer_name, domain,
                              sector, module_name, detailed_requirement,
                              standard_custom, technical_details,
                              customer_benefit, repo_id, user_email):
    try:
        base_url = os.getenv('BASE_URL', 'http://10.6.102.245:4000')
        approve_url = f"{base_url}/auth/login"

        msg = Message(
            subject="[Action Required] New Solution Submitted — Approval Needed",
            recipients=[irm_email],
            cc=[user_email] if isinstance(user_email, str) else user_email
        )

        rows = [
            ("Customer Name",        customer_name,        "#ffffff"),
            ("Domain",               domain,               "#eef6f2"),
            ("Sector",               sector,               "#ffffff"),
            ("Module Name",          module_name,          "#eef6f2"),
            ("Standard / Custom",    standard_custom,      "#ffffff"),
            ("Detailed Requirement", detailed_requirement, "#eef6f2"),
            ("Technical Details",    technical_details,    "#ffffff"),
            ("Customer Benefit",     customer_benefit,     "#eef6f2"),
            ("Submitted By",         created_by,           "#ffffff"),
        ]
        table_rows = "".join(_table_row(l, v, bg) for l, v, bg in rows)
        status_row = _table_row(
            "Status",
            _status_pill("&#9203; Sent for Approval", "#fff8e1", "#b07800", "#ffe082"),
            "#eef6f2"
        )

        msg.html = f"""
        <!DOCTYPE html>
        <html>
        <body style="margin:0;padding:0;background-color:#f0f4f2;font-family:Arial,sans-serif;">
          <table cellpadding="0" cellspacing="0" border="0" width="100%"
                 style="background:#f0f4f2;padding:32px 0;">
            <tr>
              <td align="center">
                <table cellpadding="0" cellspacing="0" border="0" width="620"
                       style="max-width:620px;border-radius:12px;overflow:hidden;">

                  <!-- HEADER -->
                  <tr>
                    <td style="background:#2d5f4f;padding:28px 36px 22px;
                               border-radius:12px 12px 0 0;">
                      {_logo_block("&#9203; Action Required", "#4a7c3f", "#c8f0a0", "#5a9a4f")}
                      <p style="margin:16px 0 4px;font-size:22px;font-weight:700;color:#ffffff;
                                font-family:Arial,sans-serif;">
                        New Solution Submitted
                      </p>
                      <p style="margin:0;font-size:13px;color:rgba(255,255,255,0.75);
                                font-family:Arial,sans-serif;line-height:1.5;">
                        A solution is awaiting your review and approval
                      </p>
                    </td>
                  </tr>

                  <!-- BODY -->
                  <tr>
                    <td style="background:#f8faf9;padding:28px 36px;">
                      <p style="margin:0 0 20px;font-size:14px;color:#444444;
                                font-family:Arial,sans-serif;line-height:1.7;">
                        Hello <strong style="color:#2d5f4f;">Team</strong>,<br>
                        A new solution has been submitted by
                        <strong style="color:#2d5f4f;">{created_by}</strong>
                        and is awaiting your approval. Please review the details below and take action.
                      </p>
                      {_divider()}
                      <table cellpadding="0" cellspacing="0" border="0" width="100%"
                             style="border-collapse:collapse;margin-bottom:24px;">
                        {_table_header("Solution Details")}
                        {table_rows}
                        {status_row}
                      </table>
                      {_cta_button(approve_url, "&#10003; Review &amp; Approve", "#2d5f4f")}
                    </td>
                  </tr>

                  <!-- FOOTER -->
                  <tr><td>{_footer_block()}</td></tr>

                </table>
              </td>
            </tr>
          </table>
        </body>
        </html>
        """

        _dispatch(msg)
        current_app.logger.info(f"Approval request email sent to IRM: {irm_email}")
        return True

    except Exception as e:
        current_app.logger.error(f"Failed to send approval request email to {irm_email}: {str(e)}")
        return False


# ─── Template 2 — Solution Approved (to creator) ────────────────────────────

def send_repo_approved_email(user_email, created_by, customer_name, module_name, repo_id, irm_email):
    try:
        base_url = os.getenv('BASE_URL', 'http://10.6.102.245:4000')
        repo_url = f"{base_url}/auth/login"

        msg = Message(
            subject="Your Solution Has Been Approved — Knowledge Repository",
            recipients=[user_email] if isinstance(user_email, str) else user_email,
            cc=[irm_email] if isinstance(irm_email, str) else irm_email
        )

        rows = [
            ("Customer Name", customer_name, "#ffffff"),
            ("Module Name",   module_name,   "#eef6f2"),
        ]
        table_rows = "".join(_table_row(l, v, bg) for l, v, bg in rows)
        status_row = _table_row(
            "Status",
            _status_pill("&#10003; Approved", "#e8f5e9", "#2e7d32", "#a5d6a7"),
            "#ffffff"
        )

        msg.html = f"""
        <!DOCTYPE html>
        <html>
        <body style="margin:0;padding:0;background-color:#f0f4f2;font-family:Arial,sans-serif;">
          <table cellpadding="0" cellspacing="0" border="0" width="100%"
                 style="background:#f0f4f2;padding:32px 0;">
            <tr>
              <td align="center">
                <table cellpadding="0" cellspacing="0" border="0" width="620"
                       style="max-width:620px;border-radius:12px;overflow:hidden;">

                  <!-- HEADER -->
                  <tr>
                    <td style="background:#2d5f4f;padding:28px 36px 22px;
                               border-radius:12px 12px 0 0;">
                      {_logo_block("&#10003; Approved", "#3a7a45", "#b0ffcc", "#4a9a55")}
                      <p style="margin:16px 0 4px;font-size:22px;font-weight:700;color:#ffffff;
                                font-family:Arial,sans-serif;">
                        Solution Approved!
                      </p>
                      <p style="margin:0;font-size:13px;color:rgba(255,255,255,0.75);
                                font-family:Arial,sans-serif;line-height:1.5;">
                        Your submission has been reviewed and approved
                      </p>
                    </td>
                  </tr>

                  <!-- BODY -->
                  <tr>
                    <td style="background:#f8faf9;padding:28px 36px;">
                      <p style="margin:0 0 20px;font-size:14px;color:#444444;
                                font-family:Arial,sans-serif;line-height:1.7;">
                        Hello <strong style="color:#2d5f4f;">{created_by}</strong>,<br>
                        Great news! Your solution has been
                        <strong style="color:#2d5f4f;">approved</strong>
                        and is now live in the Knowledge Repository for the team to discover and reuse.
                      </p>
                      {_divider()}
                      <table cellpadding="0" cellspacing="0" border="0" width="100%"
                             style="border-collapse:collapse;margin-bottom:24px;">
                        {_table_header("Solution Summary")}
                        {table_rows}
                        {status_row}
                      </table>
                      {_cta_button(repo_url, "&#128193; View Your Repository", "#3a7a63")}
                    </td>
                  </tr>

                  <!-- FOOTER -->
                  <tr><td>{_footer_block()}</td></tr>

                </table>
              </td>
            </tr>
          </table>
        </body>
        </html>
        """

        _dispatch(msg)
        current_app.logger.info(f"Approval confirmation email sent to: {user_email}")
        return True

    except Exception as e:
        current_app.logger.error(f"Failed to send approved email to {user_email}: {str(e)}")
        return False


# ─── Template 3 — Solution Rejected (to creator) ────────────────────────────

def send_repo_rejected_email(user_email, created_by, customer_name, module_name, rejected_by, irm_email):
    try:
        base_url = os.getenv('BASE_URL', 'http://10.6.102.245:4000')
        repo_url = f"{base_url}/auth/login"

        msg = Message(
            subject="Your Solution Submission Was Not Approved — Knowledge Repository",
            recipients=[user_email] if isinstance(user_email, str) else user_email,
            cc=[irm_email] if isinstance(irm_email, str) else irm_email
        )

        rows = [
            ("Customer Name", customer_name, "#ffffff"),
            ("Module Name",   module_name,   "#eef6f2"),
            ("Rejected By",   rejected_by,   "#ffffff"),
        ]
        table_rows = "".join(_table_row(l, v, bg) for l, v, bg in rows)
        status_row = _table_row(
            "Status",
            _status_pill("&#10060; Rejected", "#fce4ec", "#b71c1c", "#ef9a9a"),
            "#eef6f2"
        )

        msg.html = f"""
        <!DOCTYPE html>
        <html>
        <body style="margin:0;padding:0;background-color:#f0f4f2;font-family:Arial,sans-serif;">
          <table cellpadding="0" cellspacing="0" border="0" width="100%"
                 style="background:#f0f4f2;padding:32px 0;">
            <tr>
              <td align="center">
                <table cellpadding="0" cellspacing="0" border="0" width="620"
                       style="max-width:620px;border-radius:12px;overflow:hidden;">

                  <!-- HEADER -->
                  <tr>
                    <td style="background:#2d5f4f;padding:28px 36px 22px;
                               border-radius:12px 12px 0 0;">
                      {_logo_block("&#10060; Not Approved", "#7a2d2d", "#ffaaaa", "#9a3d3d")}
                      <p style="margin:16px 0 4px;font-size:22px;font-weight:700;color:#ffffff;
                                font-family:Arial,sans-serif;">
                        Solution Not Approved
                      </p>
                      <p style="margin:0;font-size:13px;color:rgba(255,255,255,0.75);
                                font-family:Arial,sans-serif;line-height:1.5;">
                        Your submission requires further review before publishing
                      </p>
                    </td>
                  </tr>

                  <!-- BODY -->
                  <tr>
                    <td style="background:#f8faf9;padding:28px 36px;">
                      <p style="margin:0 0 20px;font-size:14px;color:#444444;
                                font-family:Arial,sans-serif;line-height:1.7;">
                        Hello <strong style="color:#2d5f4f;">{created_by}</strong>,<br>
                        Unfortunately, your solution submission has been
                        <strong style="color:#c62828;">rejected</strong>.
                        Please review the details below and resubmit with the necessary corrections.
                      </p>
                      {_divider()}
                      <table cellpadding="0" cellspacing="0" border="0" width="100%"
                             style="border-collapse:collapse;margin-bottom:24px;">
                        {_table_header("Solution Summary")}
                        {table_rows}
                        {status_row}
                      </table>
                      <!-- Note box -->
                      <table cellpadding="0" cellspacing="0" border="0" width="100%"
                             style="margin-bottom:24px;">
                        <tr>
                          <td style="border-left:3px solid #ff8a65;background:#fff3e0;
                                     padding:12px 16px;font-size:13px;color:#5d4037;
                                     font-family:Arial,sans-serif;line-height:1.6;">
                            Please log in to the Knowledge Repository, review any feedback provided,
                            and resubmit your solution with the required corrections.
                          </td>
                        </tr>
                      </table>
                      {_cta_button(repo_url, "&#8635; Review &amp; Resubmit", "#c62828")}
                    </td>
                  </tr>

                  <!-- FOOTER -->
                  <tr><td>{_footer_block()}</td></tr>

                </table>
              </td>
            </tr>
          </table>
        </body>
        </html>
        """

        _dispatch(msg)
        current_app.logger.info(f"Rejection email sent to: {user_email}")
        return True

    except Exception as e:
        current_app.logger.error(f"Failed to send rejection email to {user_email}: {str(e)}")
        return False
    
# ─── Template 4 — Download Request Approved ─────────────────────────────────

def send_download_approved_email(user_email, requested_by_name, module_name,
                                  customer_name, approved_by_name, justification):
    try:
        base_url = os.getenv('BASE_URL', 'http://10.6.102.245:4000')
        repo_url = f"{base_url}/auth/login"

        msg = Message(
            subject="Your Download Request Has Been Approved — Knowledge Repository",
            recipients=[user_email] if isinstance(user_email, str) else user_email
        )

        rows = [
            ("Module Name",   module_name,       "#ffffff"),
            ("Customer Name", customer_name,     "#eef6f2"),
            ("Approved By",   approved_by_name,  "#ffffff"),
            ("Justification", justification or "N/A", "#eef6f2"),
        ]
        table_rows = "".join(_table_row(l, v, bg) for l, v, bg in rows)
        status_row = _table_row(
            "Status",
            _status_pill("&#10003; Approved", "#e8f5e9", "#2e7d32", "#a5d6a7"),
            "#ffffff"
        )

        msg.html = f"""
        <!DOCTYPE html>
        <html>
        <body style="margin:0;padding:0;background-color:#f0f4f2;font-family:Arial,sans-serif;">
          <table cellpadding="0" cellspacing="0" border="0" width="100%"
                 style="background:#f0f4f2;padding:32px 0;">
            <tr>
              <td align="center">
                <table cellpadding="0" cellspacing="0" border="0" width="620"
                       style="max-width:620px;border-radius:12px;overflow:hidden;">

                  <!-- HEADER -->
                  <tr>
                    <td style="background:#2d5f4f;padding:28px 36px 22px;
                               border-radius:12px 12px 0 0;">
                      {_logo_block("&#10003; Approved", "#3a7a45", "#b0ffcc", "#4a9a55")}
                      <p style="margin:16px 0 4px;font-size:22px;font-weight:700;color:#ffffff;
                                font-family:Arial,sans-serif;">
                        Download Request Approved!
                      </p>
                      <p style="margin:0;font-size:13px;color:rgba(255,255,255,0.75);
                                font-family:Arial,sans-serif;line-height:1.5;">
                        Your request to download a solution has been approved
                      </p>
                    </td>
                  </tr>

                  <!-- BODY -->
                  <tr>
                    <td style="background:#f8faf9;padding:28px 36px;">
                      <p style="margin:0 0 20px;font-size:14px;color:#444444;
                                font-family:Arial,sans-serif;line-height:1.7;">
                        Hello <strong style="color:#2d5f4f;">{requested_by_name}</strong>,<br>
                        Your download request has been
                        <strong style="color:#2d5f4f;">approved</strong>.
                        You can now log in to the Knowledge Repository and download the solution.
                      </p>
                      {_divider()}
                      <table cellpadding="0" cellspacing="0" border="0" width="100%"
                             style="border-collapse:collapse;margin-bottom:24px;">
                        {_table_header("Request Details")}
                        {table_rows}
                        {status_row}
                      </table>
                      {_cta_button(repo_url, "&#8659; Download Solution", "#3a7a63")}
                    </td>
                  </tr>

                  <!-- FOOTER -->
                  <tr><td>{_footer_block()}</td></tr>

                </table>
              </td>
            </tr>
          </table>
        </body>
        </html>
        """

        _dispatch(msg)
        current_app.logger.info(f"Download approved email sent to: {user_email}")
        return True

    except Exception as e:
        current_app.logger.error(f"Failed to send download approved email to {user_email}: {str(e)}")
        return False


# ─── Template 5 — Download Request Rejected ─────────────────────────────────

def send_download_rejected_email(user_email, requested_by_name, module_name,
                                  customer_name, rejected_by_name, justification):
    try:
        base_url = os.getenv('BASE_URL', 'http://10.6.102.245:4000')
        repo_url = f"{base_url}/auth/login"

        msg = Message(
            subject="Your Download Request Was Not Approved — Knowledge Repository",
            recipients=[user_email] if isinstance(user_email, str) else user_email
        )

        rows = [
            ("Module Name",   module_name,       "#ffffff"),
            ("Customer Name", customer_name,     "#eef6f2"),
            ("Rejected By",   rejected_by_name,  "#ffffff"),
            ("Justification", justification or "N/A", "#eef6f2"),
        ]
        table_rows = "".join(_table_row(l, v, bg) for l, v, bg in rows)
        status_row = _table_row(
            "Status",
            _status_pill("&#10060; Rejected", "#fce4ec", "#b71c1c", "#ef9a9a"),
            "#ffffff"
        )

        msg.html = f"""
        <!DOCTYPE html>
        <html>
        <body style="margin:0;padding:0;background-color:#f0f4f2;font-family:Arial,sans-serif;">
          <table cellpadding="0" cellspacing="0" border="0" width="100%"
                 style="background:#f0f4f2;padding:32px 0;">
            <tr>
              <td align="center">
                <table cellpadding="0" cellspacing="0" border="0" width="620"
                       style="max-width:620px;border-radius:12px;overflow:hidden;">

                  <!-- HEADER -->
                  <tr>
                    <td style="background:#2d5f4f;padding:28px 36px 22px;
                               border-radius:12px 12px 0 0;">
                      {_logo_block("&#10060; Not Approved", "#7a2d2d", "#ffaaaa", "#9a3d3d")}
                      <p style="margin:16px 0 4px;font-size:22px;font-weight:700;color:#ffffff;
                                font-family:Arial,sans-serif;">
                        Download Request Not Approved
                      </p>
                      <p style="margin:0;font-size:13px;color:rgba(255,255,255,0.75);
                                font-family:Arial,sans-serif;line-height:1.5;">
                        Your request to download a solution was not approved
                      </p>
                    </td>
                  </tr>

                  <!-- BODY -->
                  <tr>
                    <td style="background:#f8faf9;padding:28px 36px;">
                      <p style="margin:0 0 20px;font-size:14px;color:#444444;
                                font-family:Arial,sans-serif;line-height:1.7;">
                        Hello <strong style="color:#2d5f4f;">{requested_by_name}</strong>,<br>
                        Unfortunately, your download request has been
                        <strong style="color:#c62828;">rejected</strong>.
                        You may contact the approver for more information or submit a new request.
                      </p>
                      {_divider()}
                      <table cellpadding="0" cellspacing="0" border="0" width="100%"
                             style="border-collapse:collapse;margin-bottom:24px;">
                        {_table_header("Request Details")}
                        {table_rows}
                        {status_row}
                      </table>
                      <!-- Note box -->
                      <table cellpadding="0" cellspacing="0" border="0" width="100%"
                             style="margin-bottom:24px;">
                        <tr>
                          <td style="border-left:3px solid #ff8a65;background:#fff3e0;
                                     padding:12px 16px;font-size:13px;color:#5d4037;
                                     font-family:Arial,sans-serif;line-height:1.6;">
                            If you believe this was rejected in error, please log in and
                            submit a new download request with additional justification.
                          </td>
                        </tr>
                      </table>
                      {_cta_button(repo_url, "&#8617; Submit New Request", "#c62828")}
                    </td>
                  </tr>

                  <!-- FOOTER -->
                  <tr><td>{_footer_block()}</td></tr>

                </table>
              </td>
            </tr>
          </table>
        </body>
        </html>
        """

        _dispatch(msg)
        current_app.logger.info(f"Download rejected email sent to: {user_email}")
        return True

    except Exception as e:
        current_app.logger.error(f"Failed to send download rejected email to {user_email}: {str(e)}")
        return False
    
# ─── Template 6 — Download Request Created (to Superadmin) ──────────────────

def send_download_request_email(superadmin_email, requested_by_name, user_email,
                                 module_name, customer_name, justification,
                                 ):
    try:
        base_url = os.getenv('BASE_URL', 'http://10.6.102.245:4000')
        action_url = f"{base_url}/auth/login"

        
        

        msg = Message(
            subject="[Action Required] New Download Request — Knowledge Repository",
            recipients=[superadmin_email] if isinstance(superadmin_email, str) else superadmin_email,
            cc=[user_email] if user_email else []
        )

        rows = [
            ("Requested By",  requested_by_name,    "#ffffff"),
            ("Module Name",   module_name,           "#eef6f2"),
            ("Customer Name", customer_name,         "#ffffff"),
            ("Justification", justification or "N/A", "#eef6f2"),
        ]
        table_rows = "".join(_table_row(l, v, bg) for l, v, bg in rows)
        status_row = _table_row(
            "Status",
            _status_pill("&#9203; Pending Approval", "#fff8e1", "#b07800", "#ffe082"),
            "#ffffff"
        )

        msg.html = f"""
        <!DOCTYPE html>
        <html>
        <body style="margin:0;padding:0;background-color:#f0f4f2;font-family:Arial,sans-serif;">
          <table cellpadding="0" cellspacing="0" border="0" width="100%"
                 style="background:#f0f4f2;padding:32px 0;">
            <tr>
              <td align="center">
                <table cellpadding="0" cellspacing="0" border="0" width="620"
                       style="max-width:620px;border-radius:12px;overflow:hidden;">

                  <!-- HEADER -->
                  <tr>
                    <td style="background:#2d5f4f;padding:28px 36px 22px;
                               border-radius:12px 12px 0 0;">
                      {_logo_block("&#9203; Action Required", "#4a7c3f", "#c8f0a0", "#5a9a4f")}
                      <p style="margin:16px 0 4px;font-size:22px;font-weight:700;color:#ffffff;
                                font-family:Arial,sans-serif;">
                        New Download Request
                      </p>
                      <p style="margin:0;font-size:13px;color:rgba(255,255,255,0.75);
                                font-family:Arial,sans-serif;line-height:1.5;">
                        A user has requested access to download a solution
                      </p>
                    </td>
                  </tr>

                  <!-- BODY -->
                  <tr>
                    <td style="background:#f8faf9;padding:28px 36px;">
                      <p style="margin:0 0 20px;font-size:14px;color:#444444;
                                font-family:Arial,sans-serif;line-height:1.7;">
                        Hello <strong style="color:#2d5f4f;">Team</strong>,<br>
                        <strong style="color:#2d5f4f;">{requested_by_name}</strong>
                        has submitted a request to download a solution from the Knowledge Repository.
                        Please review the details below and take action.
                      </p>
                      {_divider()}
                      <table cellpadding="0" cellspacing="0" border="0" width="100%"
                             style="border-collapse:collapse;margin-bottom:24px;">
                        {_table_header("Request Details")}
                        {table_rows}
                        {status_row}
                      </table>
                      {_cta_button(action_url, "&#10003; Review Request", "#2d5f4f")}
                    </td>
                  </tr>

                  <!-- FOOTER -->
                  <tr><td>{_footer_block()}</td></tr>

                </table>
              </td>
            </tr>
          </table>
        </body>
        </html>
        """

        _dispatch(msg)
        current_app.logger.info(f"Download request email sent to superadmin: {superadmin_email}")
        return True

    except Exception as e:
        current_app.logger.error(f"Failed to send download request email to {superadmin_email}: {str(e)}")
        return False
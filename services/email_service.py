from flask_mail import Mail, Message
from flask import current_app
import os

mail = Mail()

def send_repo_approval_email(irm_email, created_by, customer_name, domain,
                              sector, module_name, detailed_requirement,
                              standard_custom, technical_details,
                              customer_benefit, repo_id):
    try:
        base_url = os.getenv('BASE_URL', 'http://localhost:4200')

        approve_url = f"{base_url}/auth/login"
        

        msg = Message(
            subject=f"[Action Required] New Repository Created — Approval Needed",
            recipients=[irm_email]
            
        )

        msg.html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; color: #333;">

            <h2 style="color: #0056b3;">📁 New Solution Created — Your Approval Required</h2>

            <p>Hello Team,</p>
            <p>A New Solution has been submitted by <strong>{created_by}</strong> 
               and is awaiting your approval.</p>

            <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                <tr style="background-color: #f2f2f2;">
                    <td style="padding: 10px; border: 1px solid #ddd; width: 35%;"><strong>Customer Name</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{customer_name}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Domain</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{domain}</td>
                </tr>
                <tr style="background-color: #f2f2f2;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Sector</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{sector}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Module Name</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{module_name}</td>
                </tr>
                <tr style="background-color: #f2f2f2;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Standard / Custom</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{standard_custom}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Detailed Requirement</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{detailed_requirement}</td>
                </tr>
                <tr style="background-color: #f2f2f2;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Technical Details</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{technical_details}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Customer Benefit</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{customer_benefit}</td>
                </tr>
                <tr style="background-color: #f2f2f2;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Created By</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{created_by}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Status</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">
                        <span style="color: orange; font-weight: bold;">⏳ Sent for Approval</span>
                    </td>
                </tr>
            </table>

            <p><strong>Please take action:</strong></p>
            <a href="{approve_url}" style="
                background-color: #28a745; color: white; padding: 12px 25px;
                text-decoration: none; border-radius: 5px; margin-right: 15px;
                font-weight: bold;">
                ✅ Approve
            </a>
            

            <p style="margin-top: 30px; color: #888; font-size: 12px;">
                This is an automated email from the Knowledge Repository Management System.<br>
                Please do not reply to this email.
            </p>
        </body>
        </html>
        """

        mail.send(msg)
        current_app.logger.info(f"Approval email sent to IRM: {irm_email}")
        return True

    except Exception as e:
        current_app.logger.error(f"Failed to send email to {irm_email}: {str(e)}")
        raise e
    
def send_repo_approved_email(user_email, created_by, customer_name, module_name, repo_id, irm_email):
    try:
        base_url = os.getenv('BASE_URL', 'http://localhost:4200')
        repo_url = f"{base_url}/auth/login"

        msg = Message(
            subject=f"✅ Your Solution Has Been Approved!",
            recipients=[user_email] if isinstance(user_email, str) else user_email,
            cc=[irm_email] if isinstance(irm_email, str) else irm_email 
        )

        msg.html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
            <h2 style="color: #28a745;">✅ Solution Approved Successfully</h2>

            <p>Hello <strong>{created_by}</strong>,</p>
            <p>Great news! Your solution submitted has been <strong style="color: #28a745;">Approved</strong>.</p>

            <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                <tr style="background-color: #f2f2f2;">
                    <td style="padding: 10px; border: 1px solid #ddd; width: 35%;"><strong>Customer Name</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{customer_name}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Module Name</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{module_name}</td>
                </tr>
                <tr style="background-color: #f2f2f2;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Status</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">
                        <span style="color: #28a745; font-weight: bold;">✅ Approved</span>
                    </td>
                </tr>
            </table>

            <a href="{repo_url}" style="
                background-color: #0056b3; color: white; padding: 12px 25px;
                text-decoration: none; border-radius: 5px; font-weight: bold;">
                View Your Repository
            </a>

            <p style="margin-top: 30px; color: #888; font-size: 12px;">
                This is an automated email from the Knowledge Repository Management System.<br>
                Please do not reply to this email.
            </p>
        </body>
        </html>
        """

        mail.send(msg)
        current_app.logger.info(f"Approval confirmation email sent to: {user_email}")
        return True

    except Exception as e:
        current_app.logger.error(f"Failed to send approval email to {user_email}: {str(e)}")
        raise e


def send_repo_rejected_email(user_email, created_by, customer_name, module_name, rejected_by, irm_email):
    try:
        base_url = os.getenv('BASE_URL', 'http://localhost:4200')
        repo_url = f"{base_url}/auth/login"

        msg = Message(
            subject=f"❌ Your Solution Submission Has Been Rejected",
            recipients=[user_email] if isinstance(user_email, str) else user_email,
            cc=[irm_email] if isinstance(irm_email, str) else irm_email 
        )

        msg.html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
            <h2 style="color: #dc3545;">❌ Solution Rejected</h2>

            <p>Hello <strong>{created_by}</strong>,</p>
            <p>Unfortunately, your solution submitted has been <strong style="color: #dc3545;">Rejected</strong>.</p>

            <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                <tr style="background-color: #f2f2f2;">
                    <td style="padding: 10px; border: 1px solid #ddd; width: 35%;"><strong>Customer Name</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{customer_name}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Module Name</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{module_name}</td>
                </tr>
                <tr style="background-color: #f2f2f2;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Rejected By</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{rejected_by}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Status</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">
                        <span style="color: #dc3545; font-weight: bold;">❌ Rejected</span>
                    </td>
                </tr>
            </table>

            <p>Please review your submission and resubmit with the necessary changes.</p>

            <a href="{repo_url}" style="
                background-color: #0056b3; color: white; padding: 12px 25px;
                text-decoration: none; border-radius: 5px; font-weight: bold;">
                View Your Repositories
            </a>

            <p style="margin-top: 30px; color: #888; font-size: 12px;">
                This is an automated email from the Knowledge Repository Management System.<br>
                Please do not reply to this email.
            </p>
        </body>
        </html>
        """

        mail.send(msg)
        current_app.logger.info(f"Rejection email sent to: {user_email}")
        return True

    except Exception as e:
        current_app.logger.error(f"Failed to send rejection email to {user_email}: {str(e)}")
        raise e
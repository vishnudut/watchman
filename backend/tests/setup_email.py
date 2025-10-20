#!/usr/bin/env python3
"""
Email Setup Helper for Watchman Security Scanner
Interactive script to help users configure email notifications
"""

import os
import sys
from pathlib import Path
import getpass
import smtplib
import ssl
from email.mime.text import MIMEText


def print_banner():
    """Print setup banner"""
    print("=" * 70)
    print("📧 WATCHMAN EMAIL SETUP HELPER")
    print("=" * 70)
    print("This script will help you configure email notifications")
    print("for security alerts, PR notifications, and scan summaries.")
    print("")


def get_user_input(prompt, default=None, required=True):
    """Get user input with optional default"""
    if default:
        prompt += f" (default: {default})"
    prompt += ": "

    while True:
        value = input(prompt).strip()

        if value:
            return value
        elif default:
            return default
        elif not required:
            return ""
        else:
            print("This field is required. Please enter a value.")


def get_password(prompt):
    """Get password input without echoing"""
    while True:
        password = getpass.getpass(prompt + ": ").strip()
        if password:
            return password
        print("Password is required. Please enter a value.")


def test_smtp_connection(server, port, email, password):
    """Test SMTP connection"""
    try:
        print(f"🔍 Testing connection to {server}:{port}...")

        context = ssl.create_default_context()
        with smtplib.SMTP(server, port) as smtp:
            smtp.starttls(context=context)
            smtp.login(email, password)

        print("✅ SMTP connection successful!")
        return True

    except Exception as e:
        print(f"❌ SMTP connection failed: {e}")
        return False


def send_test_email(server, port, sender_email, password, recipient_email):
    """Send a test email"""
    try:
        print(f"📧 Sending test email to {recipient_email}...")

        message = MIMEText("""
Hello!

This is a test email from Watchman Security Scanner.

If you receive this email, your email configuration is working correctly!

🛡️ Watchman Security Scanner
Automated Security Testing System
        """)

        message["Subject"] = "🧪 Watchman Test Email - Configuration Successful"
        message["From"] = f"Watchman Security Scanner <{sender_email}>"
        message["To"] = recipient_email

        context = ssl.create_default_context()
        with smtplib.SMTP(server, port) as smtp:
            smtp.starttls(context=context)
            smtp.login(sender_email, password)
            smtp.sendmail(sender_email, [recipient_email], message.as_string())

        print("✅ Test email sent successfully!")
        print(f"📨 Check {recipient_email} for the test message")
        return True

    except Exception as e:
        print(f"❌ Failed to send test email: {e}")
        return False


def get_smtp_presets():
    """Get predefined SMTP settings for popular providers"""
    return {
        "gmail": {
            "name": "Gmail",
            "server": "smtp.gmail.com",
            "port": 587,
            "instructions": """
Gmail Setup Instructions:
1. Enable 2-factor authentication on your Google account
2. Go to https://myaccount.google.com/security
3. Click on 'App passwords' (under 2-Step Verification)
4. Generate a new app password for 'Mail'
5. Use your Gmail address and the generated app password
            """
        },
        "outlook": {
            "name": "Outlook/Hotmail",
            "server": "smtp-mail.outlook.com",
            "port": 587,
            "instructions": """
Outlook Setup Instructions:
1. Use your full Outlook.com email address
2. Use your regular Outlook password
3. Make sure 'Less secure apps' is enabled if needed
            """
        },
        "yahoo": {
            "name": "Yahoo Mail",
            "server": "smtp.mail.yahoo.com",
            "port": 587,
            "instructions": """
Yahoo Setup Instructions:
1. Enable 2-factor authentication
2. Generate an app password for mail
3. Use your Yahoo email and the app password
            """
        },
        "custom": {
            "name": "Custom SMTP Server",
            "server": "",
            "port": 587,
            "instructions": """
Custom SMTP Setup:
1. Get SMTP settings from your email provider
2. Common ports: 587 (TLS), 465 (SSL), 25 (unsecured)
3. Most modern servers use port 587 with TLS
            """
        }
    }


def choose_email_provider():
    """Let user choose email provider"""
    presets = get_smtp_presets()

    print("\n📧 Choose your email provider:")
    options = list(presets.keys())

    for i, key in enumerate(options, 1):
        print(f"{i}. {presets[key]['name']}")

    while True:
        try:
            choice = input(f"\nEnter choice (1-{len(options)}): ").strip()
            choice_idx = int(choice) - 1

            if 0 <= choice_idx < len(options):
                selected_key = options[choice_idx]
                selected = presets[selected_key]

                print(f"\n✅ Selected: {selected['name']}")
                print(selected['instructions'])

                return selected_key, selected
            else:
                print("Invalid choice. Please try again.")

        except ValueError:
            print("Please enter a valid number.")


def configure_email_settings():
    """Interactive email configuration"""
    print_banner()

    # Choose provider
    provider_key, provider_config = choose_email_provider()

    print(f"\n🔧 Configuring {provider_config['name']}...")

    # Get SMTP settings
    if provider_key == "custom":
        smtp_server = get_user_input("SMTP Server")
        smtp_port = int(get_user_input("SMTP Port", "587"))
    else:
        smtp_server = provider_config["server"]
        smtp_port = provider_config["port"]
        print(f"📍 Using server: {smtp_server}:{smtp_port}")

    # Get email credentials
    print(f"\n👤 Email Credentials:")
    sender_email = get_user_input("Sender Email Address")

    if provider_key == "gmail":
        print("⚠️  Use your Gmail app password, not your regular password!")

    sender_password = get_password("Email Password/App Password")
    sender_name = get_user_input("Sender Name", "Watchman Security Scanner")

    # Get recipients
    print(f"\n📨 Email Recipients:")
    recipients = get_user_input("Notification Recipients (comma-separated)")
    admin_recipients = get_user_input("Admin Recipients (optional)", "", required=False)

    # Test connection
    print(f"\n🧪 Testing Configuration...")
    if not test_smtp_connection(smtp_server, smtp_port, sender_email, sender_password):
        print("❌ SMTP test failed. Please check your settings and try again.")
        return False

    # Ask to send test email
    send_test = input("\n📧 Send test email to verify delivery? (y/N): ").strip().lower()
    if send_test in ['y', 'yes']:
        test_recipient = input("Test email recipient: ").strip()
        if test_recipient:
            send_test_email(smtp_server, smtp_port, sender_email, sender_password, test_recipient)

    # Generate environment variables
    env_config = f"""
# Email Configuration for Watchman Security Scanner
# Generated by setup_email.py on {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# SMTP Settings
SMTP_SERVER={smtp_server}
SMTP_PORT={smtp_port}
SENDER_EMAIL={sender_email}
SENDER_PASSWORD={sender_password}
SENDER_NAME={sender_name}

# Recipients
NOTIFICATION_RECIPIENTS={recipients}"""

    if admin_recipients:
        env_config += f"\nADMIN_RECIPIENTS={admin_recipients}"

    env_config += """

# Notification Settings
NOTIFY_SECURITY_ISSUES=true
NOTIFY_PR_CREATION=true
NOTIFY_SCAN_SUMMARY=true
MIN_NOTIFICATION_SEVERITY=HIGH
"""

    # Save configuration
    print(f"\n💾 Saving Configuration...")

    # Check if .env exists
    env_file = Path(".env")
    if env_file.exists():
        backup_file = Path(".env.backup")
        print(f"📁 Backing up existing .env to {backup_file}")
        with open(env_file, 'r') as f:
            backup_content = f.read()
        with open(backup_file, 'w') as f:
            f.write(backup_content)

    # Append or create .env file
    with open(env_file, 'a') as f:
        f.write(env_config)

    # Also save as separate file
    with open("email_config.env", 'w') as f:
        f.write(env_config.strip())

    print(f"✅ Email configuration saved to:")
    print(f"   - .env (appended)")
    print(f"   - email_config.env (separate file)")

    return True


def verify_existing_config():
    """Verify existing email configuration"""
    print("🔍 Checking existing email configuration...")

    env_file = Path(".env")
    if not env_file.exists():
        print("❌ No .env file found")
        return False

    # Check for required variables
    required_vars = ["SMTP_SERVER", "SMTP_PORT", "SENDER_EMAIL", "SENDER_PASSWORD", "NOTIFICATION_RECIPIENTS"]
    missing_vars = []

    try:
        with open(env_file, 'r') as f:
            content = f.read()

        for var in required_vars:
            if f"{var}=" not in content:
                missing_vars.append(var)

        if missing_vars:
            print(f"❌ Missing email configuration variables: {', '.join(missing_vars)}")
            return False
        else:
            print("✅ Email configuration appears complete")

            # Test the configuration
            try:
                from email_handler import EmailHandler
                email_handler = EmailHandler()
                print("✅ Email handler initialization successful")
                return True
            except Exception as e:
                print(f"❌ Email handler test failed: {e}")
                return False

    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
        return False


def main():
    """Main setup function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--verify":
        verify_existing_config()
        return

    print("🚀 Starting Watchman Email Setup...")
    print("")

    # Check if config already exists
    if verify_existing_config():
        reconfigure = input("Email is already configured. Reconfigure? (y/N): ").strip().lower()
        if reconfigure not in ['y', 'yes']:
            print("✅ Using existing email configuration")
            return

    # Run configuration
    if configure_email_settings():
        print(f"\n🎉 EMAIL SETUP COMPLETE!")
        print(f"=" * 70)
        print(f"✅ Email notifications are now configured")
        print(f"✅ Security alerts will be sent via email")
        print(f"✅ PR notifications will be sent via email")
        print(f"✅ Scan summaries will be sent via email")
        print(f"")
        print(f"🎯 Next Steps:")
        print(f"1. Restart your Watchman server")
        print(f"2. Test with a repository scan")
        print(f"3. Check your email for notifications")
        print(f"")
        print(f"📧 Test email configuration anytime with:")
        print(f"   python test_email_config.py")
    else:
        print(f"\n❌ EMAIL SETUP FAILED")
        print(f"Please check your settings and try again")


if __name__ == "__main__":
    main()

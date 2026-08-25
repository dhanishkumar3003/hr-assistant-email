"""
Command-line interface for email automation.

Provides subcommands for sending invites and monitoring replies.
"""

import argparse
import logging
from sender import send_invite
from monitor import monitor_replies

log = logging.getLogger(__name__)


def setup_parser() -> argparse.ArgumentParser:
    """
    Set up and configure the argument parser.
    
    Returns:
        argparse.ArgumentParser: Configured parser with subcommands.
    """
    parser = argparse.ArgumentParser(
        description="Recruiting email sender and reply monitor"
    )
    
    subparsers = parser.add_subparsers(
        dest="command",
        required=True
    )
    
    # Send command
    send_parser = subparsers.add_parser(
        "send",
        help="Send invite to one or more candidates"
    )
    send_parser.add_argument(
        "--to",
        required=True,
        nargs="+",
        help="One or more candidate email addresses"
    )
    send_parser.add_argument(
        "--name",
        default="",
        help="Candidate name (optional)"
    )
    
    # Monitor command
    subparsers.add_parser(
        "monitor",
        help="Poll inbox for replies"
    )
    
    return parser


def handle_send_command(args) -> None:
    """
    Handle the 'send' subcommand.
    
    Sends invitations to one or more candidates and logs results.
    
    Args:
        args: Parsed command-line arguments.
    """
    successful = 0
    failed = 0
    
    for email_address in args.to:
        token = send_invite(email_address, args.name)
        
        if token:
            successful += 1
        else:
            failed += 1
    
    log.info(
        f"Send operation completed | "
        f"successful={successful} | "
        f"failed={failed}"
    )


def handle_monitor_command() -> None:
    """Handle the 'monitor' subcommand."""
    monitor_replies()


def main() -> None:
    """Parse arguments and execute appropriate command."""
    parser = setup_parser()
    args = parser.parse_args()
    
    if args.command == "send":
        handle_send_command(args)
    elif args.command == "monitor":
        handle_monitor_command()

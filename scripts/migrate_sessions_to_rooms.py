#!/usr/bin/env python3
"""Migrate existing sessions to room-based sessions.

This script converts bot-based sessions to room-based sessions for the
multi-bot architecture migration. It preserves conversation history and
maps existing sessions to their respective rooms.

Usage:
    python scripts/migrate_sessions_to_rooms.py [--dry-run] [--workspace PATH]

Options:
    --dry-run      Show what would be migrated without making changes
    --workspace    Path to workspace directory (default: ~/nanofolks)
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

from loguru import logger

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from nanofolks.config.loader import get_data_dir
from nanofolks.session.room_session_manager import RoomSession, RoomSessionManager


def setup_logging():
    """Configure logging."""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO",
    )


def find_existing_sessions(workspace: Path) -> list[Path]:
    """Find all existing session files.

    Args:
        workspace: Workspace path

    Returns:
        List of session file paths
    """
    data_dir = get_data_dir()
    sessions_dir = data_dir / "sessions"

    if not sessions_dir.exists():
        logger.info(f"No existing sessions directory found at {sessions_dir}")
        return []

    session_files = list(sessions_dir.glob("*.json"))
    logger.info(f"Found {len(session_files)} existing session files")

    return session_files


def extract_room_id_from_session(session_data: dict) -> str:
    """Extract room_id from session data.

    Args:
        session_data: Session data dict

    Returns:
        Room ID
    """
    # Try to get room_id from metadata
    room_id = session_data.get("metadata", {}).get("room_id")

    if room_id:
        return room_id

    # Try to extract from session_id
    session_id = session_data.get("session_id", "")

    # If session_id contains room info, use it
    if "room_" in session_id:
        # Extract room name from session_id
        parts = session_id.split("_")
        for i, part in enumerate(parts):
            if part == "room" and i + 1 < len(parts):
                return parts[i + 1]

    # Default to general
    return "general"


def extract_participants_from_session(session_data: dict) -> list[str]:
    """Extract bot participants from session data.

    Args:
        session_data: Session data dict

    Returns:
        List of bot names
    """
    participants = session_data.get("metadata", {}).get("participants", [])

    if participants:
        return participants

    # Try to infer from messages
    bot_names = set()
    for msg in session_data.get("messages", []):
        if msg.get("role") == "assistant":
            bot_name = msg.get("bot_name")
            if bot_name:
                bot_names.add(bot_name)

    if bot_names:
        return list(bot_names)

    # Default to leader
    return ["leader"]


async def migrate_session(
    session_file: Path,
    room_session_manager: RoomSessionManager,
    dry_run: bool = False,
) -> dict:
    """Migrate a single session file to room-based session.

    Args:
        session_file: Path to session file
        room_session_manager: RoomSessionManager instance
        dry_run: If True, don't make changes

    Returns:
        Migration result dict
    """
    result = {
        "source_file": str(session_file),
        "success": False,
        "room_id": None,
        "messages_migrated": 0,
        "errors": [],
    }

    try:
        # Load session data
        session_data = json.loads(session_file.read_text())

        # Extract room_id
        room_id = extract_room_id_from_session(session_data)
        result["room_id"] = room_id

        # Extract participants
        participants = extract_participants_from_session(session_data)

        # Get or create room session
        if dry_run:
            logger.info(f"[DRY-RUN] Would migrate session to room: {room_id}")
            room_session = RoomSession(
                room_id=room_id,
                workspace=room_session_manager.workspace,
                participants=participants,
            )
        else:
            room_session = await room_session_manager.get_session(room_id)
            # Update participants
            for bot in participants:
                if bot not in room_session.participants:
                    room_session.participants.append(bot)

        # Migrate messages
        messages = session_data.get("messages", [])
        result["messages_migrated"] = len(messages)

        if not dry_run:
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                bot_name = msg.get("bot_name") if role == "assistant" else None

                room_session.add_message(role, content, bot_name)

            # Save session
            await room_session_manager.save_session(room_id)
            logger.info(f"Migrated {len(messages)} messages to room: {room_id}")
        else:
            logger.info(f"[DRY-RUN] Would migrate {len(messages)} messages to room: {room_id}")

        result["success"] = True

    except Exception as e:
        error_msg = f"Error migrating {session_file}: {e}"
        logger.error(error_msg)
        result["errors"].append(error_msg)

    return result


async def migrate_sessions(
    workspace: Path,
    dry_run: bool = False,
) -> dict:
    """Migrate all existing sessions to room-based sessions.

    Args:
        workspace: Workspace path
        dry_run: If True, don't make changes

    Returns:
        Migration summary dict
    """
    summary = {
        "total_sessions": 0,
        "successful_migrations": 0,
        "failed_migrations": 0,
        "total_messages": 0,
        "rooms_created": set(),
        "errors": [],
    }

    # Find existing sessions
    session_files = find_existing_sessions(workspace)
    summary["total_sessions"] = len(session_files)

    if not session_files:
        logger.info("No sessions to migrate")
        return summary

    # Create room session manager
    room_session_manager = RoomSessionManager(workspace)

    # Migrate each session
    for session_file in session_files:
        result = await migrate_session(
            session_file,
            room_session_manager,
            dry_run,
        )

        if result["success"]:
            summary["successful_migrations"] += 1
            summary["total_messages"] += result["messages_migrated"]
            if result["room_id"]:
                summary["rooms_created"].add(result["room_id"])
        else:
            summary["failed_migrations"] += 1
            summary["errors"].extend(result["errors"])

    return summary


def print_summary(summary: dict, dry_run: bool = False):
    """Print migration summary.

    Args:
        summary: Migration summary dict
        dry_run: Whether this was a dry run
    """
    mode = "[DRY-RUN] " if dry_run else ""

    print(f"\n{'=' * 60}")
    print(f"{mode}Migration Summary")
    print(f"{'=' * 60}")
    print(f"Total sessions found: {summary['total_sessions']}")
    print(f"Successful migrations: {summary['successful_migrations']}")
    print(f"Failed migrations: {summary['failed_migrations']}")
    print(f"Total messages migrated: {summary['total_messages']}")
    print(f"Rooms created/updated: {len(summary['rooms_created'])}")

    if summary["rooms_created"]:
        print(f"\nRooms:")
        for room_id in sorted(summary["rooms_created"]):
            print(f"  - {room_id}")

    if summary["errors"]:
        print(f"\nErrors ({len(summary['errors'])}):")
        for error in summary["errors"][:5]:  # Show first 5 errors
            print(f"  - {error}")
        if len(summary["errors"]) > 5:
            print(f"  ... and {len(summary['errors']) - 5} more")

    print(f"{'=' * 60}\n")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Migrate existing sessions to room-based sessions")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without making changes",
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.home() / "nanofolks",
        help="Path to workspace directory (default: ~/nanofolks)",
    )

    args = parser.parse_args()

    setup_logging()

    logger.info(f"Starting session migration")
    logger.info(f"Workspace: {args.workspace}")
    logger.info(f"Mode: {'DRY-RUN' if args.dry_run else 'LIVE'}")

    if not args.dry_run:
        logger.warning("This will modify your session data. Make sure you have backups!")
        confirm = input("Continue? [y/N]: ")
        if confirm.lower() != "y":
            logger.info("Migration cancelled")
            return

    # Run migration
    summary = await migrate_sessions(args.workspace, args.dry_run)

    # Print summary
    print_summary(summary, args.dry_run)

    # Exit with appropriate code
    if summary["failed_migrations"] > 0:
        sys.exit(1)
    else:
        logger.info("Migration completed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Rename PDF files to their article titles.

This script extracts the title from the first page of each PDF in a directory
and renames the file to match the article title.
"""

import os
import subprocess
import re
from pathlib import Path


def extract_title_from_pdf(pdf_path: str) -> str | None:
    """
    Extract the article title from a PDF file.

    The title is typically found on the first page, after the line
    "Original Investigation | <category>". Titles may span multiple lines.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        The extracted title, or None if not found
    """
    try:
        # Extract text from first page only
        result = subprocess.run(
            ["pdftotext", "-f", "1", "-l", "1", "-layout", pdf_path, "-"],
            capture_output=True,
            text=True,
            check=True
        )
        text = result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return None

    # Look for "Original Investigation |" and get the title from the next lines
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if 'Original Investigation' in line:
            # Skip the category line (the line with "Original Investigation")
            # Title starts after that, potentially spanning multiple lines
            title_lines = []

            # Start collecting from the next line
            for j in range(i + 1, min(i + 6, len(lines))):
                candidate = lines[j].strip()

                # Stop if we hit an empty line (but only if we already have some title)
                if not candidate and title_lines:
                    break

                # Stop if we hit author names (patterns like "Name, MS;", "Name, MD, PhD;")
                # Author lines typically have names followed by degrees and semicolons
                if re.search(r'(?:PhD|MD|MS|ScD|MPharm|MBA|MAE|Dr)\s*;', candidate):
                    # Check if this looks like an author line (starts with name-like pattern)
                    # by seeing if it has multiple author entries (semicolons)
                    if candidate.count(';') >= 1:
                        break

                # Stop if we hit lines that are clearly not titles
                if (candidate.startswith('jamanetwork.com') or
                    candidate.startswith('http') or
                    candidate.startswith('Abstract') or
                    candidate.startswith('Key Points') or
                    re.match(r'^[A-Z]{2,3}$', candidate)):  # Category codes
                    break

                # Skip empty lines at the start
                if not candidate and not title_lines:
                    continue

                # Add this line to the title
                if candidate:
                    title_lines.append(candidate)

            if title_lines:
                # Join multi-line titles with space
                return ' '.join(title_lines)

            # Fallback: return the immediate next line
            if i + 1 < len(lines):
                return lines[i + 1].strip()

    return None


def sanitize_filename(title: str, max_length: int = 80) -> str:
    """
    Sanitize a title for use as a filename.

    Args:
        title: The title to sanitize
        max_length: Maximum length for the filename (excluding extension)

    Returns:
        A sanitized filename-safe string
    """
    # Replace invalid characters with hyphens or remove them
    # Invalid characters: / \ : * ? " < > |
    sanitized = re.sub(r'[\/\\:*?"<>|]', '-', title)

    # Replace multiple spaces/hyphens with single space/hyphen
    sanitized = re.sub(r'\s+', ' ', sanitized)
    sanitized = re.sub(r'-+', '-', sanitized)

    # Remove leading/trailing spaces and hyphens
    sanitized = sanitized.strip().strip('-')

    # Truncate if too long, adding "...." suffix
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length - 4] + '....'

    return sanitized


def rename_pdfs_in_directory(directory: str, dry_run: bool = False) -> None:
    """
    Rename all PDF files in a directory to their article titles.

    Args:
        directory: Path to the directory containing PDFs
        dry_run: If True, print what would be renamed without doing it
    """
    dir_path = Path(directory)

    if not dir_path.is_dir():
        print(f"Error: {directory} is not a valid directory")
        return

    pdf_files = list(dir_path.glob('*.pdf'))

    if not pdf_files:
        print(f"No PDF files found in {directory}")
        return

    print(f"Found {len(pdf_files)} PDF files\n")

    renamed_count = 0
    for pdf_path in pdf_files:
        print(f"Processing: {pdf_path.name}")

        title = extract_title_from_pdf(str(pdf_path))

        if not title:
            print(f"  Could not extract title, skipping\n")
            continue

        print(f"  Title: {title}")

        new_filename = sanitize_filename(title) + '.pdf'
        new_path = dir_path / new_filename

        # Check if target file already exists
        if new_path.exists() and new_path != pdf_path:
            print(f"  Target file already exists: {new_filename}")
            print(f"  Skipping to avoid overwrite\n")
            continue

        if dry_run:
            print(f"  Would rename to: {new_filename}\n")
        else:
            try:
                os.rename(pdf_path, new_path)
                print(f"  Renamed to: {new_filename}")
                renamed_count += 1
            except OSError as e:
                print(f"  Error renaming: {e}\n")
            else:
                print()

    print(f"\nSummary: Renamed {renamed_count} of {len(pdf_files)} files")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Rename PDF files to their article titles'
    )
    parser.add_argument(
        'directory',
        nargs='?',
        default='jama_network_open_papers',
        help='Directory containing PDF files (default: jama_network_open_papers)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Print what would be renamed without actually renaming'
    )

    args = parser.parse_args()

    rename_pdfs_in_directory(args.directory, args.dry_run)

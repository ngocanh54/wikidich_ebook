#!/usr/bin/env python3
"""
Main CLI entry point for Wikidich Ebook Creator.
"""
import argparse
import os
import sys
from wikidich_ebook import (
    download_n_make_ebook_wikidich,
    check_if_updated,
    get_toc,
    download_truyen,
    make_ebook
)


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description='Download Vietnamese web novels from wikicv.org (and compatible sites) and create EPUB ebooks'
    )

    parser.add_argument(
        'url',
        nargs='?',
        help='URL of the book\'s table of contents page (not needed with --epub-only --book-folder)'
    )

    parser.add_argument(
        '--book-folder',
        help='With --epub-only: build the EPUB from this already-downloaded book folder (no URL needed)'
    )

    parser.add_argument(
        '--start-chapter',
        type=int,
        default=0,
        help='Chapter number to start from (default: 0 - from beginning)'
    )

    parser.add_argument(
        '--volume-structure',
        choices=['auto', 'yes', 'no'],
        default='auto',
        help='Use volume structure in EPUB TOC (default: auto-detect)'
    )

    parser.add_argument(
        '--check-only',
        action='store_true',
        help='Only check for updates without downloading'
    )

    parser.add_argument(
        '--toc-only',
        action='store_true',
        help='Only extract table of contents'
    )

    parser.add_argument(
        '--download-only',
        action='store_true',
        help='Only download chapters (assumes TOC exists)'
    )

    parser.add_argument(
        '--epub-only',
        action='store_true',
        help='Only create EPUB (assumes chapters are downloaded)'
    )

    parser.add_argument(
        '--pages',
        type=str,
        help='Comma-separated list of page numbers for manual pagination (e.g., "1,2,3,4,5")'
    )

    args = parser.parse_args()

    if args.book_folder and not args.epub_only:
        parser.error('--book-folder only works together with --epub-only')
    if not args.url and not (args.epub_only and args.book_folder):
        parser.error('a book URL is required (or use --epub-only --book-folder PATH)')

    # Parse volume structure option
    volume_structure = None
    if args.volume_structure == 'yes':
        volume_structure = True
    elif args.volume_structure == 'no':
        volume_structure = False

    # Parse manual pagination
    page_list = None
    is_manual = False
    if args.pages:
        page_list = [int(p.strip()) for p in args.pages.split(',')]
        is_manual = True

    try:
        if args.check_only:
            # Only check for updates
            is_updated, folder = check_if_updated(args.url)
            if is_updated:
                print(f"\n✓ Updates detected! Folder: {folder}")
            else:
                print(f"\n✓ No updates. Folder: {folder}")

        elif args.toc_only:
            # Only extract TOC
            is_updated, folder = check_if_updated(args.url)
            get_toc(
                args.url,
                folder,
                check_pagination=(page_list is not None),
                page_list=page_list,
                is_manual=is_manual
            )
            print("\n✓ TOC extracted successfully!")

        elif args.download_only:
            # Only download chapters
            is_updated, folder = check_if_updated(args.url)
            download_truyen(folder, args.start_chapter)
            print("\n✓ Chapters downloaded successfully!")

        elif args.epub_only:
            # Only create EPUB; a book folder needs no URL and no network
            if args.book_folder:
                folder = os.path.abspath(args.book_folder)
                os.chdir(os.path.dirname(folder))  # EPUB is written next to the book folder
            else:
                is_updated, folder = check_if_updated(args.url)
            make_ebook(folder, args.start_chapter, volume_structure)
            print("\n✓ EPUB created successfully!")

        else:
            # Full workflow
            download_n_make_ebook_wikidich(
                args.url,
                args.start_chapter,
                volume_structure
            )

    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

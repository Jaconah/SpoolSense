export const APP_VERSION = '1.0.0'

export interface ChangelogEntry {
  version: string
  name: string
  date: string
  highlights: string[]
}

export const CHANGELOG: ChangelogEntry[] = [
  {
    version: '1.0.0',
    name: 'Public Release',
    date: 'Feb 23, 2026',
    highlights: [
      'SpoolSense is now publicly available as a self-hosted Docker image — no account or cloud service required',
      'Single-password auth with auto-generated JWT secrets on first run — zero configuration needed to get started',
      'Available on Docker Hub as jaconah/spoolsense',
    ],
  },
  {
    version: '0.7.5',
    name: 'Webhooks, Email Change & Account Deletion',
    date: 'Feb 22, 2026',
    highlights: [
      'Webhook notifications now support any HTTPS endpoint — not just Discord. Choose which events trigger a notification: order due soon, order status changed, and low stock alerts',
      'You can now change your email address from your Profile page — a verification link is sent to the new address and your existing sessions are revoked on confirmation',
      'Self-service account deletion is now available in the Danger Zone on your Profile page — accounts are soft-deleted immediately and permanently removed after 30 days',
    ],
  },
  {
    version: '0.7.4',
    name: 'Security Hardening & Two-Factor Authentication',
    date: 'Feb 21, 2026',
    highlights: [
      'Two-factor authentication (TOTP) is now available — enable it from your Profile → Security tab using any authenticator app (Google Authenticator, Authy, 1Password, etc.)',
      'Backup recovery codes are generated when you enable 2FA so you can still access your account if you lose your device',
      'Password strength meter added to all password fields — shows real-time feedback on length, uppercase, lowercase, and number requirements',
      'Rate limit errors (429) now display a clear message with a retry countdown instead of a generic failure',
      'CSV spool imports now reject non-CSV files, reject entries with extreme weights or costs, and require valid UTF-8 encoding',
    ],
  },
  {
    version: '0.7.3',
    name: 'Search, Filters & Data Export',
    date: 'Feb 19, 2026',
    highlights: [
      'All list pages (Spools, Orders, Print Jobs, Hardware, Projects) now have search, filtering, and pagination — no more loading everything at once',
      'Spool detail pages now show a full usage history — see every print job and order that consumed filament from a given spool',
      'Export your data as CSV from the Settings page — spools, print jobs, orders, hardware, and projects are all available for download',
    ],
  },
  {
    version: '0.7.2',
    name: 'Multi-Color Order Fixes',
    date: 'Feb 18, 2026',
    highlights: [
      'Orders can now specify multi-color spool usage directly — each spool\'s quantity and position are recorded with a cost snapshot for accurate P&L',
      'Creating a print job from an order now works for multi-color orders — all spools are deducted correctly and the print job is fully linked',
      'Editing a multi-color print job now supports replacing its spool entries — inventory is automatically restored from old spools and deducted from new ones',
      'Converting a multi-color print job to a project template now preserves each filament type and gram amount as individual filament entries',
    ],
  },
  {
    version: '0.7.1',
    name: 'Reliability & Error Alerting',
    date: 'Feb 15, 2026',
    highlights: [
      'Critical failures — like a database write error or a failed email send — now trigger an instant alert so problems are caught before they go unnoticed',
      'Improved internal error coverage across all core features: orders, spools, print jobs, hardware, projects, and more',
    ],
  },
  {
    version: '0.7.0',
    name: 'Data Integrity & Historical Accuracy',
    date: 'Feb 15, 2026',
    highlights: [
      'Order P&L is now fully locked in at creation — filament grams and print time are snapshotted so editing a project template no longer changes historical cost calculations',
      'Order hardware history is preserved even if a hardware item is later deleted from your catalog — the item name and brand are recorded at the time the order is placed',
      'Orders with deleted hardware items now show a clear warning badge in the edit form instead of a broken dropdown',
    ],
  },
  {
    version: '0.6.0',
    name: 'One-Off Hardware',
    date: 'Feb 14, 2026',
    highlights: [
      'Add ad-hoc hardware costs to orders without requiring a tracked inventory item — perfect for one-time purchases like a bag of screws or a specific fastener',
      'Hardware is now fully manageable when creating or editing an order, including quantity and cost adjustments',
      'Inventory items used in orders continue to deduct stock automatically when the order is marked finished',
    ],
  },
  {
    version: '0.5.1',
    name: 'What\'s New',
    date: 'Feb 14, 2026',
    highlights: [
      'Introduced this update tracker — release notes are now stored per account so you see them on every device you log in from',
      'Dashboard spool cards are now read-only — head to the Spools page to make changes',
      'Print jobs linked to an order no longer show the "Move to Inventory" button',
    ],
  },
]

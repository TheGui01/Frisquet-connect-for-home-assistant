# Changelog

## [2.5.2] - 2026-01-22

### Fixed
- Fix re-authentication error "email/password requis" by moving credentials to the root of the config entry.
- Added automatic migration (v1 -> v1.2) to fix existing configurations where credentials were hidden in `zone1`.
- Cleaned up duplicate keys in config flow.

### Added
- Added "Configure" button support in Home Assistant UI to allow updating email and password without reinstalling.

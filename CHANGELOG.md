# Changelog

## v7

- Added Support for more tags using the SteamSpy API
- Added automatic retries for API calls
- Added `search_results` metric

## v6

- Fixed a bug where the default language would be C.UTF8
- Changed environment variable `LANG` to `R2S_LANG`
- Implemented `R2S_LOG_LEVEL` environment variable that controls logging verbosity. See possible values [here](https://docs.python.org/3/library/logging.html#logging-levels).
- Made cache apply on forwarded request url instead of original request url
- Fixed internal server error for games without screenshots

## v5

- Improved DateParser - Fixes [Phalcode/rawg-to-steam-redirect#1](https://github.com/Phalcode/rawg-to-steam-redirect/issues/1)
- Made Cache support multiple languages

## v4

- Implemented Database Cache
- Implemented Stats API
- Improved String Sanitizer
- Improved Boxart Selection
- Use ISO datetime format for Release Date

## v3

- Support for Developers
- Support for Publishers
- Support for Tags (Categories)
- Support for Genres
- Support for Release Date
- Support for multiple languages
- Better Selection of Background Image
- Better Description Texts
- Dropped Support for Steam Web API Key as query parameter `key`

## v2

- Support for Steam Web API as query parameter `key`

## v1

- Initial release by [Toylerr](https://github.com/Toylerrr)

# Third-party notices

## IBM Plex Sans SC (fonts in the ipk)

- **Source:** [IBM/plex releases — Sans SC](https://github.com/IBM/plex/releases?q=sc) (`@ibm/plex-sans-sc@1.1.0`)
- **License:** [SIL Open Font License 1.1](https://scripts.sil.org/OFL)
- **In the ipk:** `etc/gl_screen/language/ttf/license.txt` is copied from the IBM package at build time.

Redistributed font binaries (`*_zh-cn.ttf`) are produced in CI/local tooling from IBM Plex Sans SC with adjusted vertical metrics only. They are **not** committed to this repository.

The ipk includes IBM’s `license.txt` (SIL OFL 1.1) under `etc/gl_screen/language/ttf/`.

## GL.iNet UI strings (`sources/en`, `sources/zh_cn`)

English keys/values are derived from the supplied `gl_screen/language/text/default` snapshot for the purpose of community localization. Existing translations and the packaging approach are based on the MIT-licensed `tutugreen/gl-screen-e5800-i18n-zh-cn` project; new firmware keys were translated locally.

- **Trademark:** “GL.iNet” and product names are trademarks of their respective owners.
- **Affiliation:** This project is **not affiliated with, endorsed by, or sponsored by** GL.iNet.
- **Firmware:** Do not redistribute GL.iNet firmware images from this repository.

Chinese translations in `sources/zh_cn` are contributed under the same [MIT License](LICENSE) as the project tooling unless noted otherwise.

## Stock device font metrics (`config/device-font-metrics.json`)

Numeric vertical metrics were measured from the stock TTF files in the supplied `gl_screen` snapshot. Only metrics are stored in git (not the original font binaries).

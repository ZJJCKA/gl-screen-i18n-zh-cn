# gl-screen-i18n-zh-cn

适用于 GL.iNet `gl_screen` 屏幕界面的非官方简体中文 OpenWrt `ipk` 汉化包。

本项目面向 GL.iNet GL-BE10000 的 `gl_screen` 屏幕程序，不是 LuCI 汉化包。包内包含屏幕语言文件、中文字体和一个 55 字节的版本锁定补丁；安装钩子会先备份 `/usr/bin/gl_screen`，再修补其中绕过语言文件的 `Toggle Button` 与 `No Function` 硬编码文本，同时汉化动态拨动开关提示、统一中文日期格式并修正中文标签布局。

## 兼容性

- 基础包依赖：`gl-sdk4-screen-large (= git-2026.100.30570-94326f1-1)`
- 原始语言文件 SHA-256：`d8d8a4ea59d2a5c2a60a9d8f4544c2aaa15c3313410b4de349e0b6670227ccf5`
- 原始 `/usr/bin/gl_screen` SHA-256：`a9b910792f20b27e948704eb50dadf3de5a553f42a64868ee978e810688a0285`
- 补丁后 `/usr/bin/gl_screen` SHA-256：`6071a43a08b87932d06518d3350c4b4bb8a348b59b9d59feb88073381e414cc8`
- 翻译条目：900 个键；另修复了原文件中粘连在同一行的两个键
- 字体：IBM Plex Sans SC，使用设备原字体的纵向指标重新生成；轻量版由四个字体角色共享一份完整中文字库

安装前脚本会同时核对原始语言文件和屏幕程序哈希。二进制版本不匹配时一定拒绝安装，不能用强制变量绕过；补丁先在临时副本上应用并核对结果哈希，再通过原子重命名替换运行文件。

## 安装

从 GitHub Releases 或 Actions 构建产物下载 `ipk`，上传到路由器后执行：

```sh
opkg install /tmp/gl-screen-i18n-zh-cn_<版本>_all.ipk
```

安装时会：

1. 把原始 `/etc/gl_screen/language/text/default` 备份为 `default.opkg-dist`；
2. 安装中文语言文件与 1 个完整中文字体，四个字体角色共用该字库；
3. 覆盖当前 `default` 语言文件；
4. 备份并定点修补 `/usr/bin/gl_screen`，把硬编码标题改为“拨动开关设置”、硬编码选项改为“无功能”；
5. 备份并汉化 `screen_disp_switch`，使未配置功能时的动态提示显示“无功能”；
6. 备份三套布局文件，把日期改为 `%s%d日`，把“锁定屏幕”按 64px 宽居中，并将主屏幕卡片及其二级页面标题统一为“USB共享”；
7. 重启 `/etc/init.d/gl_screen`。

卸载时会同时恢复原始语言、原始 `/usr/bin/gl_screen`、`screen_disp_switch` 和三套布局：

```sh
opkg remove gl-screen-i18n-zh-cn
```

`GL_SCREEN_I18N_FORCE=1` 只允许绕过语言文件哈希，不会绕过屏幕二进制哈希：

```sh
GL_SCREEN_I18N_FORCE=1 opkg install /tmp/gl-screen-i18n-zh-cn_<版本>_all.ipk
```

## 本地构建

```sh
python -m pip install -r requirements.txt
python scripts/prepare_overlay.py
python scripts/validate_zh_cn.py
python scripts/build_ipk.py
```

`build_ipk.py` 在没有 `opkg-build`/`ipkg-build` 时会使用内置的跨平台构建器，因此可直接在 Windows 上生成兼容 OpenWrt 21.02 的外层 `tar.gz` 格式 `ipk`。

## 来源与许可

包结构、已有翻译和字体处理方案参考了 [tutugreen/gl-screen-e5800-i18n-zh-cn](https://github.com/tutugreen/gl-screen-e5800-i18n-zh-cn)。详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) 与 [LICENSE](LICENSE)。本项目与 GL.iNet 无隶属或背书关系。

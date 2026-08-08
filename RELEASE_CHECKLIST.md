# Release checklist

## 构建前

- [ ] `sources/en` 与目标固件的 `/etc/gl_screen/language/text/default` 相符
- [ ] 更新 `package/scripts/preinst` 中的 `EXPECTED_SHA256`
- [ ] `/usr/bin/gl_screen` 与 `build_gl_screen_patch.py` 的原始 SHA-256 相符
- [ ] `build_gl_screen_patch.py --verify-binary <gl_screen>` 通过
- [ ] `python scripts/validate_zh_cn.py` 通过
- [ ] `python scripts/prepare_overlay.py` 成功生成 1 个共享静态界面字形子集和语言文件
- [ ] 共享字体小于 300 KB，并覆盖完整汉化词典与四个国内运营商名称
- [ ] 精简范围不包含中文 SSID；动态 SSID 按定稿使用英文或数字
- [ ] `python scripts/build_ipk.py` 成功生成 `dist/*.ipk`
- [ ] `python scripts/validate_ipk.py dist/<package>.ipk` 完整通过

## 包结构

- [ ] IPK 外层为 OpenWrt 21.02 接受的 `tar.gz`，成员顺序为 `debian-binary`、`data.tar.gz`、`control.tar.gz`
- [ ] `control.tar.gz` 中的 `preinst`、`postinst`、`postrm` 为 0755
- [ ] `data.tar.gz` 只包含语言、字体和 55 字节 `gl_screen.patch`
- [ ] 包内附带 IBM Plex Sans SC 的 `license.txt`
- [ ] `control` 的架构为 `all`，依赖锁定到 `gl-sdk4-screen-large git-2026.100.30570-94326f1-1`

## 真机验证

- [ ] 匹配的原始语言哈希可正常安装
- [ ] 不匹配的语言哈希会被 `preinst` 拒绝
- [ ] 屏幕中文、换行和字体位置显示正常
- [ ] 安装后 `gl_screen` 服务已重启
- [ ] `/usr/bin/screen_disp_switch` 的动态提示已汉化且保留原脚本备份
- [ ] `/usr/bin/gl_screen` 补丁后 SHA-256 精确匹配，原版备份存在
- [ ] 两套锁屏样式均显示为“8月5日”格式，没有月日间空格
- [ ] 唤醒显示样式选项准确显示为“主题一”和“主题二”
- [ ] “拨动开关设置”标题与“无功能”选项均为精确中文，未配置功能时动态提示为“无功能”
- [ ] “锁定屏幕”四字居中，主屏幕卡片与二级页面标题均显示“USB共享”
- [ ] `opkg remove gl-screen-i18n-zh-cn` 可恢复英文、原始屏幕程序、原脚本、三套原布局并再次重启服务

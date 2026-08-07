# -*- coding: utf-8 -*-
"""Import a stock gl_screen language file and merge the zh-CN translation.

The seed translation comes from tutugreen/gl-screen-e5800-i18n-zh-cn.
New keys in the supplied firmware snapshot are translated in NEW_TRANSLATIONS.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path


KEY_RE = re.compile(r"^([A-Za-z0-9_@]+)\s+(.+)$")
PROJECT_HEADER = "// gl-screen-i18n-zh-cn"

FONT_VALUES = {
    "FONT_MEDIUM": '"default_medium_zh-cn"',
    "FONT_BOLD": '"default_medium_zh-cn"',
    "FONT_SEMIBOLD": '"default_medium_zh-cn"',
    "FONT_MONO_MEDIUM": '"default_medium_zh-cn"',
}

NEW_TRANSLATIONS = {
    "HOME_WIFI_CHECKING_LABEL_TEXT": '"Wi-Fi 检测中"',
    "HOME_ETHERNET_CARD_LABEL_TEXT": '"以太网"',
    "HOME_NETNAT_WARNING_LABEL_TEXT": '"硬件加速已启用，无法获取速率数据。"',
    "HOME_BADGE_AW_LABEL_TEXT": '"AW"',
    "HOME_BADGE_TOR_LABEL_TEXT": '"Tor"',
    "HOME_BADGE_AGH_LABEL_TEXT": '"AGH"',
    "ETHERNET_PRESET_TITLE_LABEL_TEXT": '"预设置"',
    "ETHERNET_PPPOE_USERNAME_LABEL_TEXT": '"用户名"',
    "ETHERNET_PPPOE_PASSWORD_LABEL_TEXT": '"密码"',
    "ETHERNET_TYPE_SETTING_LABEL_TEXT": '"以太网设置"',
    "ETHERNET_PPPOE_REMINDER_LABEL_TEXT": '"静态 IP 只能在管理面板\\n(%s) 中设置。"',
    "ETHERNET_NO_CABLE_ONLY_REMINDER_LABEL_TEXT": '"未检测到网线。"',
    "ETHERNET_DROPIN_GATEWAY_REMINDER_TEXT": '"旁路网关已启用。如需修改以太网设置，\\n请先在管理面板 (%s) 中禁用旁路网关。"',
    "STATUS_TOR_LINK_LABEL_TEXT": '"Tor"',
    "STATUS_ADGUARDHOME_LINK_LABEL_TEXT": '"AGH"',
    "TETHERING_REMINDER_LABEL_TEXT1": '"未找到 USB 共享网络设备。\\n请连接智能手机或 USB 调制解调器。（请确保供电规格高于 9V/3A）"',
    "ETHERNET_PORT_DROPIN_GATEWAY_WARNING_TEXT": '"启用旁路网关时不允许切换 WAN/LAN。"',
    "INITIAL_SECURE_SKIP_LABEL_TEXT": '"稍后"',
    "LOCK_SCREEN_NO_INTERNET_LABEL_TEXT": '"无互联网连接"',
    "WIFI_INTERFACE_RADIO_BANDS_TITLE_LABEL_TEXT": '"无线频段"',
    "WIFI_INTERFACE_RADIO_BANDS_ATTRIBUTE_LABEL_TEXT": '"无线频段"',
    "CLIENT_TYPE_MLO_LABEL_TEXT": '"MLO Wi-Fi"',
    "CLIENT_TYPE_MLO_GUEST_LABEL_TEXT": '"MLO 访客 Wi-Fi"',
    "CLIENT_TRAFFIC_STATISTICS_ATTRIBUTE_LABEL_TEXT": '"流量统计"',
    "SETTING_USB_MANAGEMENT_USB_PROTOCAL_3_1_LABEL_TEXT": '"USB 3.1"',
    "SETTING_PORT_MANAGEMENT_LABEL_TEXT_2": '"1 作为 %s / 2 作为 %s"',
    "SETTING_ADGUARDHOME_ATTRIBUTE_LABEL_TEXT": '"AdGuard Home"',
    "SETTING_ABOUT@FAN@TEMP_ATTRIBUTE_LABEL_TEXT": '"CPU 温度"',
    "SETTING_ABOUT@FAN@ATTRIBUTE_LABEL_TEXT": '"风扇"',
    "SETTING_ABOUT@FAN_ATTRIBUTE_LABEL_TEXT": '"风扇设置"',
    "SETTING_ABOUT@FAN@REMINDER_LABEL_TEXT": '"*CPU 温度达到阈值时风扇启动。"',
    "SETTING_ABOUT@DEVICE_USB_PROTOCOL_SWITCH_LABEL_TEXT": '"USB 协议切换"',
    "WAKE_DISPLAY_STYLE_3_OPTION_LABEL_TEXT": '"样式 3"',
    "USB_DETECTED_CELLULAR_MODEM_WARNING_LABEL_TEXT": '"检测到蜂窝调制解调器"',
    "USB_DETECTED_CELLULAR_MODEM_REMINDER_LABEL_TEXT": '"检测到外接蜂窝调制解调器，可在蜂窝网络设置中进行管理。"',
    "USB_DETECTED_USB_TETHERING_WARNING_LABEL_TEXT": '"检测到 USB 共享网络"',
    "USB_DETECTED_USB_TETHERING_REMINDER_LABEL_TEXT": '"检测到 USB 共享网络设备，可将其用作 WAN 来源。"',
    "USB_DETECTED_USB_STORAGE_WARNING_LABEL_TEXT": '"检测到 USB 存储设备"',
    "USB_DETECTED_USB_STORAGE_REMINDER_LABEL_TEXT": '"检测到 USB 存储设备。"',
    "BRIDGE_MODE_NETWORK_MODE_TITLE_TEXT": '"网络模式"',
    "BRIDGE_MODE_APPLY_BUTTON_TEXT": '"应用"',
    "SECURITY_ALWAYS_ON_ATTRIBUTE_LABEL_TEXT": '"屏幕始终亮起"',
    "SECURITY_PASSCODE_ENABLE_ATTRIBUTE_LABEL_TEXT": '"启用屏幕密码"',
    "SECURITY_DEVICE_PASSCODE_SET_TITLE_LABEL_TEXT": '"设置设备密码"',
    "SECURITY_DEVICE_PASSCODE_RE_SET_TITLE_LABEL_TEXT": '"再次输入密码"',
    "SECURITY_DEVICE_PASSCODE_CONFIRM_TITLE_LABEL_TEXT": '"确认密码"',
    "SECURITY_PASSCODE_DISABLE_CONFIRM_TITLE_LABEL_TEXT": '"输入密码以确认"',
    "CELLULAR_NO_MODEM_FOUND_LABEL_TEXT": '"未找到调制解调器。\\n请连接 USB 调制解调器。（请确保供电规格高于 9V/3A）"',
    "CELLULAR_DEVICE_MODEM_NAME_LABEL_TEXT": '"调制解调器名称"',
    "CELLULAR_DEVICE_MODEM_IMEI_LABEL_TEXT": '"IMEI"',
    "PORTAL_REMINDER_LABEL_TEXT": '"请先使用连接到本路由器的客户端完成认证门户登录，之后才能使用此功能。"',
    "SWITCH_BUTTON_TOGGLE_LABEL_TEXT": '"拨动开关设置"',
    "SWITCH_BUTTON_ADGUARD_HOME_LABEL_TEXT": '"AdGuard Home"',
    "SWITCH_BUTTON_REPEATER_LABEL_TEXT": '"中继"',
    "SWITCH_BUTTON_TOR_LABEL_TEXT": '"Tor"',
    "SWITCH_BUTTON_MAIN_WIFI_LABEL_TEXT": '"主 Wi-Fi"',
    "SWITCH_BUTTON_GUEST_WIFI_LABEL_TEXT": '"访客 Wi-Fi"',
    "SWITCH_BUTTON_WIFI_LABEL_TEXT": '"Wi-Fi"',
    "SWITCH_BUTTON_VPN_CLIENT_LABEL_TEXT": '"VPN 客户端"',
    "SWITCH_BUTTON_NO_FUNCTION_LABEL_TEXT": '"无功能"',
    "SWITCH_BUTTON_VPN_POLICY_LABEL_TEXT": '"VPN / %s"',
    "SWITCH_BUTTON_VPN_TUNNEL_LABEL_TEXT": '"VPN / 隧道 %s"',
    "TOR_TITLE_LABEL_TEXT": '"Tor"',
    "TOR_ENABLE_LABEL_TEXT": '"启用"',
    "TOR_STATUS_CONNECTED_TEXT": '"已连接"',
    "TOR_STATUS_CONNECTING_TEXT": '"连接中..."',
    "TOR_EXIT_NODE_TITLE_TEXT": '"自定义出口节点"',
    "TOR_WARNING_TEXT": '"*启用 Tor 后，以下功能将无法正常工作：VPN、DNS、IPv6 和 AdGuard Home。"',
    "TOR_SETTING_LIST_LABEL_TEXT": '"Tor"',
    "STATUS_EXPLANATION_TOR_LABEL_TEXT": '"Tor"',
    "STATUS_EXPLANATION_ADGUARDHOME_LABEL_TEXT": '"AdGuard Home"',
    "STATUS_EXPLANATION_EXTERNAL_STORAGE_LABEL_TEXT": '"外接存储设备"',
    "STATUS_EXPLANATION_NO_ACTIVE_LABEL_TEXT": '"当前没有活动的\\n状态指示器。"',
    "ADGUARDHOME_TITLE_LABEL_TEXT": '"AdGuard Home"',
    "ADGUARDHOME_DNS_QUERIES_CARD_LABEL_TEXT": '"DNS 查询"',
    "ADGUARDHOME_BLOCK_FILTERS_CARD_LABEL_TEXT": '"过滤器拦截"',
    "ADGUARDHOME_BLOCK_MALWARE_CARD_LABEL_TEXT": '"恶意软件/钓鱼拦截"',
    "ADGUARDHOME_BLOCK_ADULT_WEBSITES_CARD_LABEL_TEXT": '"成人网站拦截"',
    "ADGUARDHOME_ENABLE_LABEL_TEXT": '"启用"',
    "ADGUARDHOME_HANDLE_CLIENT_REQ_ENABLE_LABEL_TEXT": '"由 AdGuard Home 处理客户端请求"',
    "ADGUARDHOME_REMINDER_LABEL_TEXT": '"*启用后，客户端设备的 DNS 查询将由 AdGuard Home 直接处理，基于域名的 VPN 策略和家长控制规则将失效。"',
    "FASTSETTING_LOCK_SCREEN_LABEL_TEXT": '"锁定屏幕"',
    "FASTSETTING_SCREEN_OFF_LABEL_TEXT": '"关闭屏幕"',
    "SECURITY_PASSCODE_NOT_SET_LABEL_TEXT": '"尚未设置密码"',
    "SECURITY_PASSCODE_NOT_SET_1_LABEL_TEXT": '"屏幕密码已启用但尚未设置。返回将取消启用。"',
    "SECURITY_PASSCODE_NOT_SET_SET_LABEL_TEXT": '"立即设置"',
    "SECURITY_PASSCODE_NOT_SET_LATER_LABEL_TEXT": '"返回"',
    "HOME_INTERNET_CONNECTING_TEXT": '"连接中..."',
    "HOME_INTERNET_FAILED_TEXT": '"连接失败"',
    "HOME_INTERNET_PAUSED_TEXT": '"已暂停"',
    "HOME_INTERNET_ACTIVE_TEXT": '"活动"',
    "HOME_INTERNET_LOCKED_TEXT": '"已锁定"',
    "HOME_INTERNET_NOT_REG_TEXT": '"未注册"',
}

OVERRIDE_TRANSLATIONS = {
    "INTERNET_TETHERING_CARD_LABEL_TEXT": '"USB共享"',
    "TETHERING_TITLE_LABEL_TEXT": '"USB共享"',
    "WEEK_SUNDAY_ABBR": '"周日"',
    "WEEK_MONDAY_ABBR": '"周一"',
    "WEEK_TUESDAY_ABBR": '"周二"',
    "WEEK_WEDNESDAY_ABBR": '"周三"',
    "WEEK_THURSDAY_ABBR": '"周四"',
    "WEEK_FRIDAY_ABBR": '"周五"',
    "WEEK_SATURDAY_ABBR": '"周六"',
    "WEEK_SUNDAY_ABBR_LOWER": '"周日"',
    "WEEK_MONDAY_ABBR_LOWER": '"周一"',
    "WEEK_TUESDAY_ABBR_LOWER": '"周二"',
    "WEEK_WEDNESDAY_ABBR_LOWER": '"周三"',
    "WEEK_THURSDAY_ABBR_LOWER": '"周四"',
    "WEEK_FRIDAY_ABBR_LOWER": '"周五"',
    "WEEK_SATURDAY_ABBR_LOWER": '"周六"',
    "MONTH_JANUARY_ABBR": '"1月"',
    "MONTH_FEBRUARY_ABBR": '"2月"',
    "MONTH_MARCH_ABBR": '"3月"',
    "MONTH_APRIL_ABBR": '"4月"',
    "MONTH_MAY_ABBR": '"5月"',
    "MONTH_JUNE_ABBR": '"6月"',
    "MONTH_JULY_ABBR": '"7月"',
    "MONTH_AUGUST_ABBR": '"8月"',
    "MONTH_SEPTEMBER_ABBR": '"9月"',
    "MONTH_OCTOBER_ABBR": '"10月"',
    "MONTH_NOVEMBER_ABBR": '"11月"',
    "MONTH_DECEMBER_ABBR": '"12月"',
    "SETTING_USB_MANAGEMENT_USB_PROTOCAL_3_0_LABEL_TEXT": '"USB 3.0"',
    "WIFI_ENVIRONMENT_REMINDER_LABEL_TEXT": '"*根据法规要求，户外使用时 Wi-Fi 必须切换至“户外”模式，这可能会缩小覆盖范围。"',
}


def read_key_values(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        match = KEY_RE.match(line)
        if match:
            values[match.group(1)] = match.group(2)
    return values


def clean_stock_lines(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    fixed: list[str] = []
    bad = 'TOR_SETTING_LIST_LABEL_TEXT "Tor"STATUS_EXPLANATION_FAST@CHARGING_LABEL_TEXT "Fast Charging"'
    for line in lines:
        if line == bad:
            fixed.extend(
                [
                    'TOR_SETTING_LIST_LABEL_TEXT "Tor"',
                    'STATUS_EXPLANATION_FAST@CHARGING_LABEL_TEXT "Fast Charging"',
                ]
            )
        else:
            fixed.append(line)
    return fixed


def write_lf(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("stock", type=Path, help="Stock /etc/gl_screen/language/text/default")
    parser.add_argument("seed_zh", type=Path, help="Existing zh_cn file used as a translation seed")
    parser.add_argument("--out-en", type=Path, required=True)
    parser.add_argument("--out-zh", type=Path, required=True)
    args = parser.parse_args()

    seed = read_key_values(args.seed_zh)
    en_lines = clean_stock_lines(args.stock)
    zh_lines: list[str] = []
    missing: list[str] = []

    for line in en_lines:
        if line.startswith("//"):
            zh_lines.append(PROJECT_HEADER if not zh_lines else line)
            continue
        if not line.strip():
            zh_lines.append(line)
            continue
        match = KEY_RE.match(line)
        if not match:
            raise SystemExit(f"Malformed stock line: {line!r}")
        key, stock_value = match.groups()
        value = (
            FONT_VALUES.get(key)
            or OVERRIDE_TRANSLATIONS.get(key)
            or NEW_TRANSLATIONS.get(key)
            or seed.get(key)
        )
        if value is None:
            # Font aliases and other symbolic references are language neutral.
            if not stock_value.startswith('"'):
                value = stock_value
            else:
                missing.append(key)
                continue
        zh_lines.append(f"{key} {value}")

    if missing:
        raise SystemExit("Missing translations: " + ", ".join(missing))

    write_lf(args.out_en, en_lines)
    write_lf(args.out_zh, zh_lines)
    print(f"Wrote {args.out_en} ({len(en_lines)} lines)")
    print(f"Wrote {args.out_zh} ({len(zh_lines)} lines)")


if __name__ == "__main__":
    main()

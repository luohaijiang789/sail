"""真浏览器端到端验证：登录后逐个访问页面，捕获 JS 报错与网络失败。"""
import sys
from playwright.sync_api import sync_playwright

BASE = "http://localhost:5779"

PAGES = [
    ("Dashboard", "/dashboard/analytics"),
    ("仓库管理", "/repositories"),
    ("扫描列表", "/scans"),
    ("扫描详情", "/scans/2"),
    ("API 资产", "/api-assets"),
    ("漏洞清单", "/findings"),
]


def main():
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()

        page.on("console", lambda msg: errors.append(f"[console.{msg.type}] {msg.text}") if msg.type in ("error",) else None)
        page.on("pageerror", lambda exc: errors.append(f"[pageerror] {exc}"))
        page.on("requestfailed", lambda req: errors.append(f"[requestfailed] {req.url}"))

        # 1. 登录（已关闭滑块验证，选 Super 自动填充账密后点登录）
        print("=== 登录 ===")
        page.goto(f"{BASE}/auth/login", wait_until="networkidle")
        page.wait_for_timeout(2000)
        try:
            page.locator('span:has-text("Super")').first.click(timeout=3000)
            page.wait_for_timeout(800)
        except Exception:
            pass
        try:
            # Playwright page.click 在 vben 登录按钮上被 html 拦截 pointer events，
            # 用 JS 原生 click 触发表单提交。
            page.evaluate("""() => {
                const btn = document.querySelector('button[aria-label="login"]');
                if (btn) btn.click();
            }""")
        except Exception as e:
            errors.append(f"[登录] 按钮点击失败: {e}")
        page.wait_for_timeout(4000)
        url = page.url
        print(f"  登录后 URL: {url}")
        if "/auth/login" in url:
            errors.append("[登录失败] 仍在登录页")

        # 2. 逐个访问页面
        for name, path in PAGES:
            print(f"\n=== {name} {path} ===")
            try:
                page.goto(f"{BASE}{path}", wait_until="networkidle", timeout=15000)
                page.wait_for_timeout(2500)
                body_text = page.inner_text("body")
                has_data = any(k in body_text for k in [
                    "WebGoat", "SUCCEEDED", "sql-injection", "GET", "POST",
                    "总扫描", "漏洞", "仓库", "扫描", "EXTERNAL_CODEQL",
                ])
                has_empty = "暂无" in body_text or "404" in body_text[:100]
                print(f"  有数据: {has_data}  空状态: {has_empty}")
                if not has_data and not has_empty:
                    print(f"  body: {body_text[:200].strip()}")
                if has_empty and not has_data:
                    errors.append(f"[{name}] 页面空")
            except Exception as e:
                errors.append(f"[{name}] 访问失败: {e}")
                print(f"  访问失败: {e}")

        browser.close()

    print("\n" + "=" * 50)
    if errors:
        print(f"发现 {len(errors)} 个问题:")
        for e in errors[:30]:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("✅ 全部页面通过，无 JS 报错/网络失败")


if __name__ == "__main__":
    main()

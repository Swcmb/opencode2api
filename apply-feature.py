from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
REPO = Path.cwd()

if not (REPO / "go.mod").is_file() or not (REPO / "cmd/opencode2api/main.go").is_file():
    raise SystemExit("请在 opencode2api 仓库根目录运行此脚本。")


def replace_exact(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: 预期找到 1 处，实际找到 {count} 处；为避免覆盖错误版本，已停止。")
    path.write_text(text.replace(old, new), encoding="utf-8")

main = REPO / "cmd/opencode2api/main.go"
replace_exact(
    main,
    '''import (\n\t"context"\n\t"flag"\n''',
    '''import (\n\t"context"\n\t"flag"\n\t"fmt"\n''',
    "main.go import",
)
replace_exact(
    main,
    '''\t"opencode2api/internal/gateway"\n\t"opencode2api/internal/telemetry"\n''',
    '''\t"opencode2api/internal/gateway"\n\t"opencode2api/internal/telemetry"\n\t"opencode2api/internal/updater"\n''',
    "main.go updater import",
)
replace_exact(
    main,
    '''func main() {\n\tbuildinfo.Version = version\n\tconfigPath := flag.String("config", "config.json", "path to config.json")\n''',
    '''func main() {\n\tif updater.IsHelper(os.Args) {\n\t\tif err := updater.RunHelper(os.Args[2:]); err != nil {\n\t\t\tfmt.Fprintln(os.Stderr, "update helper failed:", err)\n\t\t\tos.Exit(1)\n\t\t}\n\t\treturn\n\t}\n\n\tbuildinfo.Version = version\n\tgenerateKey := flag.Bool("generate-key", false, "generate a high-entropy local API key and exit")\n\tconfigPath := flag.String("config", "config.json", "path to config.json")\n''',
    "main.go startup",
)
replace_exact(
    main,
    '''\tflag.Parse()\n\n\tcfg, err := config.Load(*configPath)\n''',
    '''\tflag.Parse()\n\n\tif *generateKey {\n\t\tkey, err := config.GenerateAPIKey()\n\t\tif err != nil {\n\t\t\tslog.Error("failed to generate API key", "error", err)\n\t\t\tos.Exit(1)\n\t\t}\n\t\tfmt.Println(key)\n\t\treturn\n\t}\n\n\tcfg, err := config.Load(*configPath)\n''',
    "main.go generate-key",
)
replace_exact(
    main,
    '''\tdefer manager.Shutdown()\n\n\tapiServer := &http.Server{\n''',
    '''\tdefer manager.Shutdown()\n\n\tupdater.Start(ctx, updater.Options{\n\t\tCurrentVersion: buildinfo.Version,\n\t\tExecutable:     "",\n\t\tArgs:           os.Args[1:],\n\t\tLogger:         logger,\n\t\tOnRestart:      cancel,\n\t})\n\n\tapiServer := &http.Server{\n''',
    "main.go updater start",
)

api_keys = REPO / "internal/admin/api_keys.go"
replace_exact(
    api_keys,
    '''import (\n\t"crypto/rand"\n\t"encoding/hex"\n\t"errors"\n''',
    '''import (\n\t"errors"\n''',
    "api_keys.go imports",
)
replace_exact(
    api_keys,
    '''\tkey := input.Value\n\tif key == "" {\n\t\tvar random [24]byte\n\t\tif _, err := rand.Read(random[:]); err != nil {\n\t\t\twriteAdminError(w, 500, "generation_failed", "无法生成密钥")\n\t\t\treturn\n\t\t}\n\t\tkey = "sk-local-" + hex.EncodeToString(random[:])\n\t}\n\t_, err := a.manager.Update(func(cfg *config.Config) error { return addAPIKey(cfg, strings.TrimSpace(input.Name), key) })\n''',
    '''\tkey := input.Value\n\tif key == "" {\n\t\tvar err error\n\t\tkey, err = config.GenerateAPIKey()\n\t\tif err != nil {\n\t\t\twriteAdminError(w, 500, "generation_failed", "无法生成密钥")\n\t\t\treturn\n\t\t}\n\t}\n\tname := strings.TrimSpace(input.Name)\n\tif name == "" {\n\t\tname = "自动生成 Key"\n\t}\n\t_, err := a.manager.Update(func(cfg *config.Config) error { return addAPIKey(cfg, name, key) })\n''',
    "api_keys.go generation",
)

index = REPO / "webui/index.html"
replace_exact(
    index,
    '''                  <label for="api-key-name">名称</label
                  ><input
                    id="api-key-name"
                    placeholder="例如：我的笔记助手"
                    maxlength="80"
                    required
                  />''',
    '''                  <label for="api-key-name">名称（可选）</label
                  ><input
                    id="api-key-name"
                    placeholder="留空自动使用“自动生成 Key”"
                    maxlength="80"
                  />''',
    "index.html key name field",
)
replace_exact(index, '<button id="api-key-create" class="primary">创建 API Key</button>', '<button id="api-key-create" class="primary">一键生成高熵 API Key</button>', "index.html key button")

for relative in [
    "internal/config/keygen.go",
    "internal/config/keygen_test.go",
    "internal/updater/updater.go",
    "internal/updater/updater_test.go",
]:
    source = ROOT / "files" / relative
    destination = REPO / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)

try:
    gofmt = shutil.which("gofmt")
    if gofmt:
        changed = [
            str(main),
            str(api_keys),
            str(REPO / "internal/config/keygen.go"),
            str(REPO / "internal/config/keygen_test.go"),
            str(REPO / "internal/updater/updater.go"),
            str(REPO / "internal/updater/updater_test.go"),
        ]
        subprocess.run([gofmt, "-w", *changed], check=True)
except subprocess.CalledProcessError as exc:
    raise SystemExit(f"gofmt 失败：{exc}")

print("已应用：")
print("  - 内置跨平台自动更新：Linux/Windows/macOS × amd64/arm64")
print("  - 默认每 6 小时检查，首次启动后 2 分钟检查")
print("  - GitHub Release ZIP/TAR.GZ + SHA256 校验")
print("  - Windows/Unix 自更新辅助进程、启动失败回滚")
print("  - -generate-key 一键生成 256 bit 高熵本地 API Key")
print("  - WebUI 一键生成高熵 API Key，名称可留空")
print("\n环境变量：")
print("  OPENCODE2API_AUTO_UPDATE=0|false|no|off   关闭自动更新")
print("  OPENCODE2API_UPDATE_INTERVAL_HOURS=1..168  修改检查周期")
print("\n建议验证：go test ./...")

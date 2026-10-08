# opencode2api：内置自动更新 + 高熵 API Key

## 修改内容

自动更新直接编译进 `opencode2api`，不再依赖旁路 PowerShell/Bash 更新器。

支持仓库现有全部发布目标：

- linux/amd64
- linux/arm64
- windows/amd64
- windows/arm64
- darwin/amd64
- darwin/arm64

启动后首次检查延迟 2 分钟，之后默认每 6 小时检查一次。只处理比当前版本更新的正式 Release；下载后校验 `.sha256`，Windows 使用独立的临时 helper 解决正在运行的 EXE 无法覆盖问题，Linux/macOS 也统一经过 helper 完成替换和重启。

新版本启动失败会恢复 `.bak` 并重新启动旧版本。自动更新不会覆盖 `config.json`。

自动更新环境变量：

```powershell
$env:OPENCODE2API_AUTO_UPDATE = "0"
$env:OPENCODE2API_UPDATE_INTERVAL_HOURS = "12"
```

API Key 使用 `crypto/rand` 生成 32 字节随机数据，编码为 URL-safe Base64，并增加 `sk-local-` 前缀，共提供 256 bit 随机熵。

命令行：

```powershell
.\opencode2api.exe -generate-key
```

WebUI 的 API Key 页面可以不填写名称，直接点击「一键生成高熵 API Key」。自定义 Key 的旧入口仍然保留。

## 应用

```powershell
cd C:\path\to\opencode2api
python .\apply-feature.py
```

随后：

```powershell
go test ./...
go build -o opencode2api.exe .\cmd\opencode2api
```

## 设计边界

更新使用 GitHub Releases 的公开下载地址和 SHA256 文件；SHA256 提供传输完整性校验，发布仓库本身的可信性仍由 GitHub 仓库权限与发布流程保证。

自动更新要求运行账户对 `opencode2api` 所在目录有写权限。以 root/systemd、Windows 服务等受保护方式安装到只读系统目录时，应将可执行文件部署到服务账户可写的目录，或者通过环境变量关闭自动更新。

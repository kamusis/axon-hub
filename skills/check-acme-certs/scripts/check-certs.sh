#!/usr/bin/env bash
# ============================================================================
# 证书健康检查脚本
#
# 用途：检查 acme.sh 管理的所有证书剩余有效期。
#       如果剩余天数低于阈值，说明 acme.sh 续期出现问题，发出告警。
#
# 阈值说明：
#   acme.sh 默认在到期前 60 天触发续期。续期成功时，证书剩余天数
#   会被重置回 ~90 天；续期失败时，剩余天数会单调递减。
#   因此只要续期一直成功，剩余天数永远 >= 60 天。
#   我们设阈值为 55 天，留 5 天缓冲用于 acme.sh 重试 / 人工介入。
#
# 退出码：
#   0 = 所有证书正常
#   1 = 发现异常（剩余天数低于阈值 / 证书缺失 / 证书损坏）
# ============================================================================

set -u

ACME_DIR="${ACME_DIR:-$HOME/.acme.sh}"
LOG_FILE="${LOG_FILE:-$ACME_DIR/cert-check.log}"
THRESHOLD_DAYS="${CERT_CHECK_THRESHOLD:-55}"

# ----------- 工具函数 -----------
log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S %z')] $*"
    if [ -n "$LOG_FILE" ] && [ -w "$(dirname "$LOG_FILE")" 2>/dev/null ]; then
        echo "$msg" >> "$LOG_FILE"
    fi
}

alert() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S %z')] ❌ $*"
    if [ -n "$LOG_FILE" ] && [ -w "$(dirname "$LOG_FILE")" 2>/dev/null ]; then
        echo "$msg" | tee -a "$LOG_FILE" >&2
    else
        echo "$msg" >&2
    fi
}

ok() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S %z')] ✅ $*"
    if [ -n "$LOG_FILE" ] && [ -w "$(dirname "$LOG_FILE")" 2>/dev/null ]; then
        echo "$msg" | tee -a "$LOG_FILE"
    else
        echo "$msg"
    fi
}

# ----------- 初始化 -----------
EXIT_CODE=0

log "========== 开始证书健康检查 (阈值=${THRESHOLD_DAYS}天) =========="

if [ ! -d "$ACME_DIR" ]; then
    alert "acme.sh 目录不存在: $ACME_DIR"
    exit 1
fi

# ----------- 遍历所有证书 -----------
# acme.sh 目录结构: ~/.acme.sh/<domain>_<keytype>/<domain>.cer
# 例如: ~/.acme.sh/dev.kamusis.me_ecc/dev.kamusis.me.cer
#
# 用 -mindepth 2 -maxdepth 2 限定只匹配两级目录下的 .cer 文件，
# 并排除 ca.cer / fullchain.cer / nginx.fullchain.cer 等组合证书，
# 只检查叶子证书（域名证书）。

checked=0
while IFS= read -r -d '' cert_file; do
    checked=$((checked + 1))

    # 从路径中提取域名: ~/.acme.sh/<domain>_<keytype>/<domain>.cer
    dir_path="$(dirname "$cert_file")"
    domain="$(basename "$dir_path" | sed -E 's/_ecc$|_rsa$//')"

    # 解析证书到期时间
    not_after="$(openssl x509 -in "$cert_file" -noout -enddate 2>/dev/null | sed 's/^notAfter=//')"

    if [ -z "$not_after" ]; then
        alert "证书解析失败: $cert_file"
        EXIT_CODE=1
        continue
    fi

    # 计算剩余天数
    expiry_ts="$(date -d "$not_after" +%s 2>/dev/null)"
    if [ -z "$expiry_ts" ]; then
        alert "无法解析证书到期时间 [$domain]: $not_after"
        EXIT_CODE=1
        continue
    fi

    now_ts="$(date +%s)"
    days_left="$(( (expiry_ts - now_ts) / 86400 ))"

    if [ "$days_left" -lt "$THRESHOLD_DAYS" ]; then
        alert "证书剩余天数过低: $domain 还有 ${days_left} 天 (阈值=${THRESHOLD_DAYS}) 到期=$not_after"
        EXIT_CODE=1
    else
        ok "$domain 剩余 ${days_left} 天, 到期=$not_after"
    fi
done < <(find "$ACME_DIR" -mindepth 2 -maxdepth 2 -type f -name "*.cer" \
         ! -name "ca.cer" \
         ! -name "fullchain.cer" \
         ! -name "nginx.fullchain.cer" \
         -print0)

if [ "$checked" -eq 0 ]; then
    alert "未在 $ACME_DIR 下找到任何证书文件"
    EXIT_CODE=1
fi

# ----------- 总结 -----------
if [ "$EXIT_CODE" -eq 0 ]; then
    log "✅ 检查完成: 共 $checked 个证书，全部正常"
    echo "✅ 检查完成: 共 $checked 个证书，全部正常"
else
    alert "检查完成: 共 $checked 个证书, 存在异常 (exit=1)"
fi

exit $EXIT_CODE

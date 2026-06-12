#!/bin/bash
# ── MiniPlane SSL 证书初始化脚本 ─────────────────────────────
# 用法:
#   1. 将下面的 domains 改为你的真实域名
#   2. 确保域名 DNS 已指向服务器 IP
#   3. 运行: bash nginx/init-letsencrypt.sh
#   4. 然后: docker compose up -d

domains=(example.com)          # ← 改成你的域名
email=""                       # ← 改成你的邮箱 (可选)
staging=0                      # 设为 1 测试 (不会触发速率限制)

rsa_key_size=4096
data_path="./data/certbot"

if [ -d "$data_path" ]; then
  read -p "已有证书数据，是否覆盖? (y/N) " decision
  if [ "$decision" != "Y" ] && [ "$decision" != "y" ]; then
    exit
  fi
fi

# ── 生成 dhparam ────────────────────────────────────────────
if [ ! -e "$data_path/ssl-dhparams.pem" ]; then
  echo "### 生成 dhparam (请耐心等待)..."
  mkdir -p "$data_path"
  openssl dhparam -out "$data_path/ssl-dhparams.pem" 2048
fi

# ── 创建临时 nginx 容器获取证书 ─────────────────────────────
for domain in "${domains[@]}"; do
  echo "### 为 $domain 创建临时证书..."
  mkdir -p "$data_path/conf/live/$domain"
done

# ── 启动临时 nginx 做域名验证 ──────────────────────────────
docker compose -f docker-compose.yml up -d nginx
echo "### 等待 nginx 就绪..."
sleep 5

# ── 请求证书 ────────────────────────────────────────────────
for domain in "${domains[@]}"; do
  certbot_cmd="docker compose -f docker-compose.yml run --rm certbot certonly --webroot \
    --webroot-path=/var/www/certbot \
    --email $email \
    --domains $domain \
    --rsa-key-size $rsa_key_size \
    --agree-tos \
    --force-renewal"

  if [ $staging -eq 1 ]; then
    certbot_cmd="$certbot_cmd --staging"
  fi

  eval "$certbot_cmd"
done

echo "### 证书获取完成！重启 nginx 加载证书..."
docker compose restart nginx
echo "### 完成！"

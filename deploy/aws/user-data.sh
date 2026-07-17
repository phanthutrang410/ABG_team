#!/bin/bash
set -euxo pipefail
dnf update -y
dnf install -y docker
systemctl enable --now docker

REGION=ap-southeast-1
ACCOUNT=058264284502
API_IMAGE="${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/silent-shield-api:d4a"
WEB_IMAGE="${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/silent-shield-web:d4a"
# Elastic IP reserved for D4a Live shell
PUBLIC_IP=52.74.255.88
FE_ORIGIN="http://${PUBLIC_IP}:3000"

# IAM/ECR readiness
for i in $(seq 1 30); do
  if aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com"; then
    break
  fi
  sleep 10
done

docker pull "$API_IMAGE"
docker pull "$WEB_IMAGE"

docker rm -f silent-shield-api silent-shield-web || true

docker run -d --name silent-shield-api --restart unless-stopped \
  -p 8000:8000 \
  -e APP_ENV=demo \
  -e CORS_ORIGINS="$FE_ORIGIN" \
  "$API_IMAGE"

docker run -d --name silent-shield-web --restart unless-stopped \
  -p 3000:3000 \
  "$WEB_IMAGE"

echo "D4a shell ready IP=${PUBLIC_IP} api=${API_IMAGE} web=${WEB_IMAGE}" > /var/log/silent-shield-d4a.txt

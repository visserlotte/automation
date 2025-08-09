#!/usr/bin/env bash
set -euo pipefail
export AWS_REGION="${AWS_REGION:-us-east-1}"
export AWS_ID="${AWS_ID:-035636365017}"
ECR_URL="${AWS_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/master-ai"

aws ecr describe-repositories --repository-name master-ai --region "$AWS_REGION" >/dev/null 2>&1 || \
  aws ecr create-repository --repository-name master-ai --region "$AWS_REGION"

aws ecr get-login-password --region "$AWS_REGION" | \
  docker login --username AWS --password-stdin "$ECR_URL"

TAG="v$(date +%Y%m%d%H%M%S)"
docker build --no-cache -t master-ai:$TAG .
docker tag master-ai:$TAG "$ECR_URL:$TAG"
docker push "$ECR_URL:$TAG"

aws lambda update-function-code --function-name master-ai --image-uri "$ECR_URL:$TAG"
aws lambda wait function-updated --function-name master-ai

aws lambda invoke --cli-binary-format raw-in-base64-out \
  --function-name master-ai \
  --payload '{"task":"ping"}' \
  resp.json >/dev/null && cat resp.json

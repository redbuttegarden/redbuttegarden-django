#!/bin/bash
set -e

ENV=$1
ACTION=$2

if [ "$ACTION" == "up" ]; then
  terraform -chdir=terraform init
  terraform -chdir=terraform apply -var-file=terraform_${ENV}.tfvars -auto-approve
  python update_zappa_vpc.py $ENV
  zappa deploy $ENV
elif [ "$ACTION" == "down" ]; then
  zappa undeploy $ENV -y
  terraform -chdir=terraform destroy -var-file=terraform_${ENV}.tfvars -auto-approve
else
  echo "Usage: ./deploy.sh [environment] [up|down]"
fi
